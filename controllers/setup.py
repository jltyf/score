import sys
import os
from PyQt5 import QtWidgets
import time
import requests
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
    for try_count in range(retry_times+1):
        time_now = get_time()
        if time_now == -1:
            if try_count == retry_times:
                msg_box = QMessageBox(QMessageBox.Warning, '警告', '未能验证软件有效期，请检查网络')
                msg_box.exec_()
                sys.exit()
            time.sleep(0.7)
        elif time_now > time.strptime('2024/10/1 00:00:00', "%Y/%m/%d %H:%M:%S"):
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
        hea = {'User-Agent': 'Mozilla/5.0'}
        url = r'http://time1909.beijing-time.org/time.asp'
        r = requests.get(url=url, headers=hea)
        if r.status_code == 200:
            result = r.text
            data = result.split(";")
            year = data[1][len("nyear") + 3: len(data[1])]
            month = data[2][len("nmonth") + 3: len(data[2])]
            day = data[3][len("nday") + 3: len(data[3])]
            hrs = data[5][len("nhrs") + 3: len(data[5])]
            minute = data[6][len("nmin") + 3: len(data[6])]
            sec = data[7][len("nsec") + 3: len(data[7])]
            beijin_time_str = "%s/%s/%s %s:%s:%s" % (year, month, day, hrs, minute, sec)
            beijin_time = time.strptime(beijin_time_str, "%Y/%m/%d %H:%M:%S")
            return beijin_time
    except:
        return -1


if __name__ == '__main__':
    app_start()
