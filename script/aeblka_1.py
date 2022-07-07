import xml.etree.ElementTree as ET
import math

from button_tool.py.vtdTools import Weather


def get_score(xml_path, weather_result):
    require_weather = Weather.SNOW
    if require_weather == weather_result:
        weather_score = True
    else:
        weather_score = False
    try:
        item = 1
        score = 0
        distance = 0
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for player in root.iter('Player'):
            for des in player.iter('Description'):
                if des.attrib['Name'] == 'Ego':
                    for ego_init in player.iter('Init'):
                        for ego_data in ego_init:
                            if ego_data.tag == 'Speed':
                                ego_speed = float(ego_data.attrib['Value'])
                            elif ego_data.tag == 'PosAbsolute':
                                ego_direction = float(ego_data.attrib['Direction'])

                elif des.attrib['Name'] == 'veh_1':
                    for veh_init in player.iter('Init'):
                        for veh_data in veh_init:
                            if veh_data.tag == 'Speed':
                                veh_speed = float(veh_data.attrib['Value'])
                            elif veh_data.tag == 'PosRelative':
                                if veh_data.attrib['Pivot'] == 'Ego':
                                    distance = float(veh_data.attrib['Distance'])
        for player_actions in root.iter('PlayerActions'):
            if player_actions.attrib['Player'] == 'veh_1':
                for speed_change in player_actions.iter('SpeedChange'):
                    veh_acc = float(speed_change.attrib['Rate'])
                    veh_acc_target = float(speed_change.attrib['Target'])

        if ego_speed == 80 / 3.6 and ego_direction == math.radians(5):
            score += 2
            xml_score_detail = f'{item}.测试车以80km/h且初始车头方向偏离车道5°,得2分;<br/>'
        else:
            xml_score_detail = f'{item}.不满足测试车以80km/h且初始车头方向偏离车道5°,不得分;<br/>'
        item += 1
        if veh_speed == 40 / 3.6 and abs(distance) == 300 and veh_acc == 3 and veh_acc_target == 0:
            score += 2
            xml_score_detail = xml_score_detail + f'{item}.障碍车初始速度等于40km/h且与测试车车距等于300m,障碍车减速度等于3m/s²且减速至静止,得2分;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.不满足障碍车初始速度等于40km/h且与测试车车距等于300m,障碍车减速度等于3m/s²且减速至静止,不得分;<br/>'
        item += 1
        return score, xml_score_detail, weather_score, item
    except:
        return 0, '场景文件格式错误，场景修改得0分;<br/>', weather_score, 1
