import os
from configparser import ConfigParser
from xml.etree import ElementTree

cfg = ConfigParser()
cfg.read(os.path.join(os.path.join(os.path.expanduser('~'), 'dist'), "setting.ini"))
print(cfg.items())
setting_data = dict(cfg.items("dev"))


def get_launch_score(launch_path):
    try:
        tree = ElementTree.parse(launch_path)
        root = tree.getroot()
        return 1, '算法参数文件格式正确,得1分'
    except:
        return 0, '算法参数文件格式不正确,不得分'
    # launch_score = 1
    # return launch_score
