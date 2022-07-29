import sys
import os
from PyQt5 import QtWidgets
import time
import requests
import json
from PyQt5.QtWidgets import QMessageBox

sys.path.append('../')
from controllers.exam import MainWindow
from controllers.login import LoginWindow
from configparser import ConfigParser

cfg = ConfigParser()
cfg.read(os.path.join(os.path.join(os.path.expanduser('~'), 'dist'), "setting.ini"))
setting_data = dict(cfg.items("dev"))


def app_start(retry_times=5):
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    longin_window = LoginWindow(main_window)
    for try_count in range(retry_times + 1):
        time_now = get_time()
        if time_now == -1:
            if try_count == retry_times:
                msg_box = QMessageBox(QMessageBox.Warning, '警告', '未能验证软件有效期，请检查网络')
                msg_box.exec_()
                sys.exit()
            time.sleep(0.7)
        elif int(time_now) > int(time.mktime(time.strptime('2024/10/1 00:00:00', "%Y/%m/%d %H:%M:%S"))):
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '软件已过期')
            msg_box.exec_()
            sys.exit()
        else:
            longin_window.show()
            sys.exit(app.exec_())


def app_restart():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def get_time():
    try:
        url = r'http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp'
        r = requests.get(url=url, timeout=2)
        if r.status_code == 200:
            result = json.loads(r.text)
            beijin_time = result['data']['t'][0:10]
            return beijin_time
    except:
        return -1


if __name__ == '__main__':
    app_start()
