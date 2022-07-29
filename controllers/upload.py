import json
import os
import requests
from minio import Minio
from configparser import ConfigParser
import time
import shutil
from xml.etree import ElementTree
from controllers.launch_score import get_launch_score
from controllers.xml_score import get_xml_score

cfg = ConfigParser()
cfg.read(os.path.join(os.path.join(os.path.expanduser('~'), 'dist'), "setting.ini"))
setting_data = dict(cfg.items("dev"))
client = Minio(
    endpoint=setting_data['endpoint'],
    access_key=setting_data['access key'],
    secret_key=setting_data['secret key'],
    secure=False
)


def get_config(config_path):
    radar_dict = {'sensor_id': 11}
    camera_dict = {'sensor_id': 16}
    lidar_dict = {'sensor_id': 21}
    try:
        tree = ElementTree.parse(config_path)
        root = tree.getroot()

        for sensor in root.iter('Sensor'):
            if sensor.get('name') == 'Front_Radar':
                pos_xyz = sensor.get('posXyz').split(' ')
                pos_hpr = sensor.get('posHpr').split(' ')
                radar_dict = {'sensor_id': 11, 'pos_x': 1000 * float(pos_xyz[0]), 'pos_y': 1000 * float(pos_xyz[1]),
                              'pos_z': 1000 * float(pos_xyz[2]),
                              'pos_h': float(pos_hpr[0]), 'pos_p': float(pos_hpr[1]), 'pos_r': float(pos_hpr[2])}
            elif sensor.get('name') == 'Front_Camera':
                pos_xyz = sensor.get('posXyz').split(' ')
                pos_hpr = sensor.get('posHpr').split(' ')
                camera_dict = {'sensor_id': 16, 'pos_x': 1000 * float(pos_xyz[0]), 'pos_y': 1000 * float(pos_xyz[1]),
                               'pos_z': 1000 * float(pos_xyz[2]),
                               'pos_h': float(pos_hpr[0]), 'pos_p': float(pos_hpr[1]), 'pos_r': float(pos_hpr[2])}
            elif sensor.get('name') == 'Lidar':
                pos_xyz = sensor.get('posXyz').split(' ')
                pos_hpr = sensor.get('posHpr').split(' ')
                lidar_dict = {'sensor_id': 21, 'pos_x': 1000 * float(pos_xyz[0]), 'pos_y': 1000 * float(pos_xyz[1]),
                              'pos_z': 1000 * float(pos_xyz[2]),
                              'pos_h': float(pos_hpr[0]), 'pos_p': float(pos_hpr[1]), 'pos_r': float(pos_hpr[2])}
        return [radar_dict, camera_dict, lidar_dict]
    except:
        return [radar_dict, camera_dict, lidar_dict]


def upload2minio(student_id, token, exam_id, weather_result):
    ts = time.time()
    minio_path = f'tmp/{student_id}_{ts}'
    xml_score, xml_score_detail, weather_score, item = get_xml_score(exam_id, weather_result)
    if weather_score:
        xml_score += 1
        score_detail = f'{item}.场景天气符合要求,得1分。'
    else:
        score_detail = f'{item}.场景天气不符合要求,不得分。'
    xml_score_detail = xml_score_detail + score_detail
    xml_root_path = os.path.join(os.path.expanduser('~'), setting_data['xml path'])
    xml_path = os.path.join(xml_root_path, f'{exam_id}.xml')
    launch_root_path = os.path.join(os.path.expanduser('~'), setting_data['launch path'])
    launch_path = os.path.join(launch_root_path, 'summary.launch')
    launch_score, launch_detail = get_launch_score(launch_path)
    minio_xml_path = os.path.join(minio_path, xml_path.split('/')[-1])
    minio_launch_path = os.path.join(minio_path, launch_path.split('/')[-1])

    log_path = os.path.join(os.path.expanduser('~'), 'dist/scpMsg.log')
    minio_log_path = os.path.join(minio_path, log_path.split('/')[-1])
    client.fput_object(setting_data['bucket name'], minio_log_path, log_path)
    client.fput_object(setting_data['bucket name'], minio_xml_path, xml_path)
    client.fput_object(setting_data['bucket name'], minio_launch_path, launch_path)

    url = setting_data['routing address'] + '/api/v1/task'
    configurations = get_config(os.path.join(os.path.expanduser('~'), setting_data['config user path']))
    headers = {"Authorization": token}
    res = requests.post(url=url, headers=headers, json={"student_id": student_id,
                                                        "xml_path": minio_xml_path,
                                                        "launch_path": minio_launch_path,
                                                        "part1_score": xml_score,
                                                        "part1_desc": xml_score_detail,
                                                        "part2_score": launch_score,
                                                        "part2_desc": launch_detail,
                                                        "log_path": minio_log_path,
                                                        "configurations": configurations})
    if json.loads(res.text)['code'] == 200:
        demo_path = os.path.join(xml_root_path, 'TrafficDemo.xml')
        temp_path = os.path.join(os.path.join(os.path.expanduser('~'), setting_data['download path']),
                                 'TrafficDemo.xml')
        shutil.copy(demo_path, temp_path)
        shutil.rmtree(xml_root_path, ignore_errors=True)
        os.mkdir(xml_root_path)
        shutil.copy(temp_path, demo_path)
        shutil.rmtree(launch_root_path, ignore_errors=True)
        os.mkdir(launch_root_path)
        return True
    else:
        return False
