import json
import os
import shutil
import subprocess
import sys
import threading
import time
from configparser import ConfigParser

import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtWidgets import QMessageBox
from minio import Minio

from button_tool.py.vtdTools import stopVtd, startVtd, WeatherDetector, Weather
from controllers.upload import upload2minio
from views.MainWindow import Ui_ExamWindow

cfg = ConfigParser()
cfg.read(os.path.join(os.path.join(os.path.expanduser('~'), 'dist'), "setting.ini"))
setting_data = dict(cfg.items("dev"))
client = Minio(
    endpoint=setting_data['endpoint'],
    access_key=setting_data['access key'],
    secret_key=setting_data['secret key'],
    secure=False
)


class MainWindow(QtWidgets.QMainWindow, Ui_ExamWindow):
    _instance_lock = threading.Lock()

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.token = None
        self.exam_data = None
        # self.exit.clicked.connect(self.__del__)
        self.exit.clicked.connect(self.closeEvent)
        self.vtd_ip = "127.0.0.1"
        self.vtd_port = 48179
        self.vtd_start_script = os.path.join(os.path.expanduser('~'), setting_data['vtd start script'])
        self.vtd_stop_script = os.path.join(os.path.expanduser('~'), setting_data['vtd stop script'])
        self.weather_require = None
        self.weather_result = Weather.DEFAULT
        self.sensors_info = None
        self.vtd_start_flag = False
        self.edit_algo_flag = False
        self.abs_path = os.path.abspath(os.getcwd())
        self.submit_button = add_style(self.submit_button)
        self.vtd_start = add_style(self.vtd_start)
        self.vtd_quit = add_style(self.vtd_quit)
        self.algo_start = add_style(self.algo_start)
        self.algo_quit = add_style(self.algo_quit)
        self.exit = add_style(self.exit)
        self.minio_launch_path = None
        self.close_flag = True
        background_img = QPixmap(os.path.join(os.path.expanduser('~'), setting_data['background1']))
        background_img = background_img.scaled(self.width(), self.height())
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(background_img))
        self.setPalette(palette)

        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setGeometry(QtCore.QRect(0, 0, 207, 51))
        self.logo.setObjectName("logo")
        self.logo.setPixmap(QPixmap(os.path.join(os.path.expanduser('~'), setting_data['logo'])))

    def closeEvent(self, event):
        if self.close_flag:
            messageBox = QMessageBox(QMessageBox.Question, self.tr("提示"), self.tr("退出后修改的部分将被全部重置,是否确认退出程序？"),
                                     QMessageBox.NoButton,
                                     self)
            yr_btn = messageBox.addButton(self.tr("是"), QMessageBox.YesRole)
            messageBox.addButton(self.tr("否"), QMessageBox.NoRole)
            messageBox.exec_()
            if messageBox.clickedButton() == yr_btn:
                if self.vtd_start_flag:
                    self.wd.stop()
                    self.wd.join(2)
                    os.chdir(os.path.join(os.path.expanduser('~'), 'VIRES/VTD.2021.3/bin/'))
                    stopVtd(self.vtd_stop_script)
                    os.chdir(self.abs_path)
                result = get_result("docker inspect --format='{{.State.Running}}' ros-docker")
                if result:
                    os.popen(cmd=setting_data['stop docker'])
                    os.popen(cmd=setting_data['remove docker'])
                sys.exit(0)
            else:
                try:
                    event.ignore()
                except AttributeError:
                    return

        # 是否确认退出此程序？退出后修改的部分将被全部重置！

    def __new__(cls, *args, **kwargs):
        if not hasattr(MainWindow, "_instance"):
            with MainWindow._instance_lock:
                if not hasattr(MainWindow, "_instance"):
                    MainWindow._instance = QtWidgets.QMainWindow.__new__(cls)
        return MainWindow._instance

    def set_exam(self, student_id, token):
        if self.submit_button.text() == '开始考试':
            self.change_window()
            url = setting_data['routing address'] + '/api/v1/localexam'
            headers = {'Authorization': token}
            request = requests.get(url=url, headers=headers)
            request_data = json.loads(request.text)['data']['exam']
            xml_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['xml path']),
                                    f'{request_data["score_func"]}.xml')
            launch_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['launch path']),
                                       'summary.launch')
            client.fget_object(setting_data['bucket name'], request_data['default_xml'], xml_path)
            self.minio_launch_path = request_data['default_launch']
            client.fget_object(setting_data['bucket name'], self.minio_launch_path, launch_path)
            self.exam_data = request_data
            image_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['download path']),
                                      'question.png')
            client.fget_object(setting_data['bucket name'], request_data['desc_pic'], image_path)
            exam_img = QPixmap(image_path)
            self.exam_desc.setGeometry(QtCore.QRect(50, 80, 1450, 600))
            self.exam_desc.setPixmap(exam_img)
        else:
            messageBox = QMessageBox(QMessageBox.Question, self.tr("提示"), self.tr("是否确认提交？"), QMessageBox.NoButton,
                                     self)
            yr_btn = messageBox.addButton(self.tr("是"), QMessageBox.YesRole)
            messageBox.addButton(self.tr("否"), QMessageBox.NoRole)
            messageBox.exec_()
            if messageBox.clickedButton() == yr_btn:
                if self.vtd_start_flag:
                    self.wd.stop()
                    self.wd.join(2)
                    self.weather_result = self.wd.latestWeather
                exam_result = upload2minio(student_id, token, self.exam_data['score_func'], self.weather_result)
                if exam_result:
                    self.close_flag = False
                    QMessageBox.information(self, "考试结束", "考题提交成功,考试完成!")
                    self.close()
                    os.chdir(os.path.join(os.path.expanduser('~'), 'VIRES/VTD.2021.3/bin/'))
                    stopVtd(self.vtd_stop_script)
                    os.chdir(self.abs_path)
                    command = setting_data['quit algo']
                    os.system(command=command)
                else:
                    msg_box = QMessageBox(QMessageBox.Critical, '错误', '上传考题失败,请重试!')
                    msg_box.exec_()
                    return
            else:
                return

    def change_window(self):
        init_vtd()
        log_path = os.path.join(os.path.expanduser('~'), 'dist/scpMsg.log')
        if os.path.exists(log_path):
            os.remove(log_path)
        with open(log_path, 'a+', encoding='utf-8') as f:
            pass
        self.submit_button.setGeometry(QtCore.QRect(650, 800, 200, 50))
        _translate = QtCore.QCoreApplication.translate
        font = QtGui.QFont()
        font.setPointSize(13)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.new_label1.sizePolicy().hasHeightForWidth())

        self.new_label1.setGeometry(QtCore.QRect(180, 645, 150, 150))
        self.new_label1.setSizePolicy(sizePolicy)
        self.new_label1.setFont(font)
        self.new_label1.setText(_translate("ExamWindow", "VTD操作"))
        self.vtd_start.setGeometry(QtCore.QRect(300, 700, 100, 40))
        self.vtd_start.setSizePolicy(sizePolicy)
        self.vtd_start.setFont(font)
        self.vtd_start.setText(_translate("ExamWindow", "启动"))
        self.vtd_start.clicked.connect(self.start_vtd_event)
        self.vtd_quit.setGeometry(QtCore.QRect(500, 700, 100, 40))
        self.vtd_quit.setSizePolicy(sizePolicy)
        self.vtd_quit.setFont(font)
        self.vtd_quit.setText(_translate("ExamWindow", "关闭"))
        self.vtd_quit.clicked.connect(self.quit_vtd_event)

        # self.new_label2.setGeometry(QtCore.QRect(750, 695, 150, 150))
        # self.new_label2.setFont(font)
        # self.new_label2.setText(_translate("ExamWindow", "传感器配置"))

        self.new_label3.setGeometry(QtCore.QRect(850, 645, 150, 150))
        self.new_label3.setFont(font)
        self.new_label3.setText(_translate("ExamWindow", "算法"))
        self.algo_start.setGeometry(QtCore.QRect(920, 700, 100, 40))
        self.algo_start.setSizePolicy(sizePolicy)
        self.algo_start.setFont(font)
        self.algo_start.setText(_translate("ExamWindow", "启动"))
        self.algo_start.clicked.connect(self.start_algo_event)
        self.algo_quit.setGeometry(QtCore.QRect(1120, 700, 100, 40))
        self.algo_quit.setSizePolicy(sizePolicy)
        self.algo_quit.setFont(font)
        self.algo_quit.setText(_translate("ExamWindow", "关闭"))
        self.configurations.setGeometry(QtCore.QRect(1320, 700, 100, 40))
        self.configurations.setSizePolicy(sizePolicy)
        self.configurations.setFont(font)
        self.configurations.setText(_translate("ExamWindow", "编辑"))
        self.configurations.clicked.connect(self.edit_algo)
        self.algo_quit.clicked.connect(self.quit_algo_event)
        font.setPointSize(12)
        self.submit_button.setText(_translate('ExamWindow', '交卷'))
        self.setFixedSize(self.width(), self.height())
        os.popen(cmd=setting_data['remove docker'])

    def start_vtd_event(self):
        self.vtd_start_flag = True
        os.chdir(os.path.join(os.path.expanduser('~'), 'VIRES/VTD.2021.3/bin/'))
        stopVtd(self.vtd_stop_script)
        os.chdir(self.abs_path)
        startVtd(self.vtd_start_script)
        self.vtd_quit = add_style(self.vtd_quit, True)
        self.vtd_start = add_style(self.vtd_start, True)
        self.wd = WeatherDetector(self.vtd_ip, self.vtd_port)
        self.wd.start()
        time.sleep(1)
        self.vtd_quit = add_style(self.vtd_quit)
        self.vtd_start = add_style(self.vtd_start)

    def quit_vtd_event(self):
        self.vtd_quit = add_style(self.vtd_quit, True)
        self.vtd_start = add_style(self.vtd_start, True)
        if self.vtd_start_flag:
            self.wd.stop()
            self.wd.join(2)
            self.weather_result = self.wd.latestWeather
            self.sensors_info = self.wd.latestSensorsInfo
            self.vtd_start_flag = False
            os.chdir(os.path.join(os.path.expanduser('~'), 'VIRES/VTD.2021.3/bin/'))
            stopVtd(self.vtd_stop_script)
            os.chdir(self.abs_path)
            time.sleep(0.5)
        self.vtd_quit = add_style(self.vtd_quit)
        self.vtd_start = add_style(self.vtd_start)

    def edit_algo(self):
        self.algo_start = add_style(self.algo_start, True)
        self.algo_quit = add_style(self.algo_quit, True)
        self.configurations = add_style(self.configurations, True)
        launch_file = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['launch path']), 'summary.launch')
        if not os.path.exists(launch_file):
            launch_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['launch path']),
                                       'summary.launch')
            client.fget_object(setting_data['bucket name'], self.minio_launch_path, launch_path)
        result = os.popen('ps aux | grep gedit').readlines()
        for process in result:
            if 'Sl' in process:
                messageBox = QMessageBox(QMessageBox.Question, self.tr("提示"), self.tr("算法文件已打开,是否重新打开(未保存的数据会丢失)?"),
                                         QMessageBox.NoButton,
                                         self)
                yr_btn = messageBox.addButton(self.tr("是"), QMessageBox.YesRole)
                messageBox.addButton(self.tr("否"), QMessageBox.NoRole)
                messageBox.exec_()
                if messageBox.clickedButton() == yr_btn:
                    os.popen(f'kill {process.split(" ")[4]}')
                    time.sleep(0.5)
                    os.popen(f"gedit {launch_file}")
                    break
                else:
                    self.algo_start = add_style(self.algo_start)
                    self.algo_quit = add_style(self.algo_quit)
                    self.configurations = add_style(self.configurations)
                    return
        os.popen(f"gedit {launch_file}")
        self.algo_start = add_style(self.algo_start)
        self.algo_quit = add_style(self.algo_quit)
        self.configurations = add_style(self.configurations)

    def start_algo_event(self):
        self.algo_start = add_style(self.algo_start, True)
        self.algo_quit = add_style(self.algo_quit, True)
        self.configurations = add_style(self.configurations, True)
        result = get_result("docker inspect --format='{{.State.Running}}' ros-docker")
        if result:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '算法已经启动，请先关闭后再启动!')
            msg_box.exec_()
            self.algo_start = add_style(self.algo_start)
            self.algo_quit = add_style(self.algo_quit)
            self.configurations = add_style(self.configurations)
            return
        command = setting_data['start algo']
        os.system(command=command)
        time.sleep(1)
        result = get_result("docker inspect --format='{{.State.Running}}' ros-docker")
        if result:
            QMessageBox.information(self, "启动", "算法启动成功!")
        else:
            os.system(command=setting_data['remove docker'])
            time.sleep(0.5)
            if get_result("docker inspect --format='{{.State.Running}}' ros-docker"):
                QMessageBox.information(self, "启动", "算法启动成功!")
            else:
                QMessageBox.information(self, "错误", "算法启动失败,请重试!")
        self.algo_start = add_style(self.algo_start)
        self.algo_quit = add_style(self.algo_quit)
        self.configurations = add_style(self.configurations)

    def quit_algo_event(self):
        self.algo_start = add_style(self.algo_start, True)
        self.algo_quit = add_style(self.algo_quit, True)
        self.configurations = add_style(self.configurations, True)
        result = get_result("docker inspect --format='{{.State.Running}}' ros-docker")
        if not result:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '算法尚未启动,请重试!')
            msg_box.exec_()
            self.algo_start = add_style(self.algo_start)
            self.algo_quit = add_style(self.algo_quit)
            self.configurations = add_style(self.configurations)
            return
        command = setting_data['quit algo']
        os.system(command=command)
        for i in range(12):
            result = get_result("docker inspect --format='{{.State.Running}}' ros-docker")
            if not result:
                QMessageBox.information(self, "关闭", "算法关闭成功!")
                self.algo_start = add_style(self.algo_start)
                self.algo_quit = add_style(self.algo_quit)
                self.configurations = add_style(self.configurations)
                return
            time.sleep(1)
        msg_box = QMessageBox(QMessageBox.Critical, '错误', '算法关闭失败,请重试!')
        msg_box.exec_()
        self.algo_start = add_style(self.algo_start)
        self.algo_quit = add_style(self.algo_quit)
        self.configurations = add_style(self.configurations)


def add_style(button, disable_flag=False):
    if disable_flag:
        button.setEnabled(False)
        button.setStyleSheet("QPushButton{color:white}"
                             "QPushButton{background-color:rgb(100,100,100)}"
                             "QPushButton{border-radius:10px}")
    else:
        button.setEnabled(True)
        button.setStyleSheet("QPushButton:hover{background-color:rgb(0,68,120)}"
                             "QPushButton:pressed{padding-left:3px}"
                             "QPushButton:pressed{padding-top:3px}"
                             "QPushButton{color:white}"
                             "QPushButton{background-color:rgb(42,93,198)}"
                             "QPushButton{border-radius:10px}")
    return button


def get_result(command):
    order = command
    pi = subprocess.Popen(order, shell=True, stdout=subprocess.PIPE)
    output = str(pi.stdout.read())
    if 'true' in output:
        result = True
    else:
        result = False
    return result


def init_vtd():
    launch_root_path = os.path.join(os.path.expanduser('~'), setting_data['launch path'])
    xml_root_path = os.path.join(os.path.expanduser('~'), setting_data['xml path'])
    demo_path = os.path.join(xml_root_path, 'TrafficDemo.xml')
    temp_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['download path']),
                             'TrafficDemo.xml')
    shutil.copy(demo_path, temp_path)
    shutil.rmtree(xml_root_path, ignore_errors=True)
    os.mkdir(xml_root_path)
    shutil.copy(temp_path, demo_path)
    shutil.rmtree(launch_root_path, ignore_errors=True)
    os.mkdir(launch_root_path)
    configurations_user = os.path.join(os.path.expanduser('~'), setting_data['config user path'])
    configurations_base = os.path.join(os.path.expanduser('~'), setting_data['config path'])
    shutil.copy(configurations_base, configurations_user)
