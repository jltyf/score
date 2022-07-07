import sys
import os
from configparser import ConfigParser

cfg = ConfigParser()
cfg.read(os.path.join(os.path.join(os.path.expanduser('~'), 'dist'), "setting.ini"))
setting_data = dict(cfg.items("dev"))


def get_xml_score(exam_id, weather_result):
    xml_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['xml path']), f'{exam_id}.xml')
    function_name = 'get_score'
    sys.path.append(os.path.join(os.path.expanduser('~'), setting_data['script path']))
    evaluate = __import__(exam_id)
    imp_function = getattr(evaluate, function_name)
    return imp_function(xml_path, weather_result)
