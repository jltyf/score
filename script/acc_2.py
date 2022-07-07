import xml.etree.ElementTree as ET
import math

from button_tool.py.vtdTools import Weather


def get_score(xml_path, weather_result):
    require_weather = Weather.RAIN
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
                                ego_start_x = float(ego_data.attrib['X'])

                elif des.attrib['Name'] == 'Car_1':
                    for veh_init in player.iter('Init'):
                        for veh_data in veh_init:
                            if veh_data.tag == 'Speed':
                                veh_speed = float(veh_data.attrib['Value'])
                            elif veh_data.tag == 'PosRelative':
                                if veh_data.attrib['Pivot'] == 'Ego':
                                    distance = float(veh_data.attrib['Distance'])
        if ego_speed == 60 / 3.6:
            xml_score_detail = f'{item}.测试车初始速度等于60km/h,得1分;<br/>'
            score += 1
        else:
            xml_score_detail = f'{item}.测试车初始速度不等于60km/h,不得分;<br/>'
        item += 1
        if ego_direction == math.radians(0):
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.测试车初始车头方向偏离车道0°,得1分;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.测试车初始车头方向偏离车道不等于0°,不得分;<br/>'
        item += 1
        if veh_speed == 30 / 3.6:
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.障碍车初速度等于30km/h,得1分;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.障碍车初速度不等于30km/h,不得分;<br/>'
        item += 1
        if abs(distance) == 150:
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.障碍车位于测试车前方150m,得1分;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.不满足障碍车位于测试车前方150m,不得分;<br/>'
        item += 1
        return score, xml_score_detail, weather_score, item
    except:
        return 0, '场景文件格式错误，场景修改得0分;<br/>', weather_score, 1
