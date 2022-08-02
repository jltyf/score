import math
import xml.etree.ElementTree as ET

from button_tool.py.vtdTools import Weather


def get_score(xml_path, weather_result):
    ego_car_type = None
    veh_car_type = None
    ego_speed = 500
    ego_direction = 500
    veh_speed = 500
    veh_start_x = 0
    veh_start_y = 0
    ego_x = 100000
    ego_y = 100000
    veh_lane = 100000
    distance = 100000
    require_weather = Weather.RAIN
    if require_weather == weather_result:
        weather_score = True
    else:
        weather_score = False
    try:
        item = 1
        score = 0
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for player in root.iter('Player'):
            for des in player.iter('Description'):
                if des.attrib['Name'] == 'Ego':
                    ego_car_type = des.attrib['Type']
                    for ego_init in player.iter('Init'):
                        for ego_data in ego_init:
                            if ego_data.tag == 'Speed':
                                ego_speed = float(ego_data.attrib['Value'])
                            elif ego_data.tag == 'PosAbsolute':
                                ego_direction = float(ego_data.attrib['Direction'])
                                ego_x = float(ego_data.attrib['X'])
                                ego_y = float(ego_data.attrib['Y'])

                elif des.attrib['Name'] == 'veh_1':
                    veh_car_type = des.attrib['Type']
                    for veh_init in player.iter('Init'):
                        for veh_data in veh_init:
                            if veh_data.tag == 'Speed':
                                veh_speed = float(veh_data.attrib['Value'])
                            elif veh_data.tag == 'PosAbsolute':
                                veh_start_x = float(veh_data.attrib['X'])
                                veh_start_y = float(veh_data.attrib['Y'])
                            elif veh_data.tag == 'PosRelative':
                                if veh_data.attrib['Pivot'] == 'Ego':
                                    distance = float(veh_data.attrib['Distance'] - (ego_x - 905))
                                    veh_lane = int(veh_data.attrib['Lane'])

        if ego_speed == 80 / 3.6 and ego_direction == math.radians(5) and ego_car_type == 'CICV_Car':
            score += 1
            xml_score_detail = f'{item}.测试车(Ego)车型为CICV_Car,以80km/h,初始车头方向偏离车道5°,进入弯道行驶,且不驶出本车道,得1分;<br/>'
        else:
            xml_score_detail = f'{item}.不满足测试车(Ego)车型为CICV_Car,以80km/h,初始车头方向偏离车道5°,进入弯道行驶,且不驶出本车道,不得分;<br/>'
        item += 1
        if 9.99 / 3.6 <= veh_speed <= 70.01 / 3.6 and 1129.64 <= veh_start_x <= 1131.59 and 175 <= veh_start_y <= 225 and veh_car_type == 'Audi_A3_2009_red':
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.障碍车(veh_1)车型为Audi_A3_2009_red,位于Ego出弯位置前方50-100m且在同一车道,以10-70km/h的速度定速行驶,得1分;<br/>'
        elif 9.99 / 3.6 <= veh_speed <= 70.01 / 3.6 and 341.35 <= distance <= 391.35 and veh_lane == 0 and veh_car_type == 'Audi_A3_2009_red':
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.障碍车(veh_1)车型为Audi_A3_2009_red,位于Ego出弯位置前方50-100m且在同一车道,以10-70km/h的速度定速行驶,得1分;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.不满足障碍车(veh_1)车型为Audi_A3_2009_red,位于Ego出弯位置前方50-100m且在同一车道,以10-70km/h的速度定速行驶,不得分;<br/>'
        item += 1
        return score, xml_score_detail, weather_score, item
    except:
        return 0, '场景文件格式错误，场景搭建得0分;<br/>', weather_score, 1


if __name__ == '__main__':
    score = get_score('/home/tang/xml/pro/real/acclka_2.xml', Weather.RAIN)
    print(score)
