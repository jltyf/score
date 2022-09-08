import os
import functools
import threading

import requests
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
import json
from minio import Minio

from views.LoginWindow import Ui_LoginWindow
from configparser import ConfigParser

cfg = ConfigParser()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cfg.read(os.path.join(os.path.join(os.path.expanduser('~'), 'dist'), "setting.ini"))
setting_data = dict(cfg.items("dev"))
client = Minio(
    endpoint=setting_data['endpoint'],
    access_key=setting_data['access key'],
    secret_key=setting_data['secret key'],
    secure=False
)
token = None


class LoginWindow(QtWidgets.QMainWindow, Ui_LoginWindow):
    _instance_lock = threading.Lock()

    def __init__(self, exam_window):
        super(LoginWindow, self).__init__()
        self.setupUi(self)

        # 将点击事件与槽函数进行连接
        self.login.clicked.connect(lambda: self.click_login(exam_window))

    def __new__(cls, *args, **kwargs):
        if not hasattr(LoginWindow, "_instance"):
            with LoginWindow._instance_lock:
                if not hasattr(LoginWindow, "_instance"):
                    LoginWindow._instance = QtWidgets.QMainWindow.__new__(cls)
        return LoginWindow._instance

    def click_login(self, exam_window):
        user = self.student_id.text()
        pwd = self.student_pwd.text()

        if not user or not pwd:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '账户和密码不能为空')
            msg_box.exec_()
            return
        url = setting_data['routing address'] + "/auth"
        request = requests.post(url=url, json={"type": "student",
                                               "student": {"name": user,
                                                           "password": pwd}})
        request_data = json.loads(request.text)
        if not request_data['code'] == 200:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '登陆失败，请和考官确认后重新输入')
            msg_box.exec_()
            return
        else:
            global token
            token = request_data['data']['token']
            student_id = request_data['data']['id']
            _translate = QtCore.QCoreApplication.translate
            exam_window.student_id.setText(_translate('ExamWindow', user))
            exam_window.submit_button.setText(_translate('ExamWindow', '开始考试'))
            image_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['download path']),
                                      'exam_desc.png')
            client.fget_object(setting_data['bucket name'], setting_data['exam desc path'], image_path)
            exam_img = QPixmap(image_path)
            exam_window.exam_desc.setPixmap(exam_img)
            exam_window.exam_desc.setScaledContents(True)
            exam_window.submit_button.clicked.connect(functools.partial(exam_window.set_exam, student_id, token))
            exam_window.show()
            self.close()
