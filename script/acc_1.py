import math
import xml.etree.ElementTree as ET

from button_tool.py.vtdTools import Weather


def get_score(xml_path, weather_result):
    ego_car_type = None
    veh_car_type = None
    ttc_pivot = None
    ego_speed = 500
    ego_direction = 500
    veh_speed = 500
    veh_acc_target = 500
    veh_lane = 1000
    ttc = 0
    veh_lane_change = 1000
    veh_lane_change_time = 1000
    veh_acc = 1000
    require_weather = Weather.SNOW
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
        # for player in root.iter('PlayerActions'):
        #     if player.attrib['Player'] == 'Ego':
        #         for action in player.iter('Action'):
        #             for scp in action.iter('SCP'):
        #                 require_weather = scp.text.split('type="')[1][:4]
        if ego_speed == 80 / 3.6 and ego_direction == math.radians(0) and ego_car_type == 'CICV_Car':
            xml_score_detail = f'{item}.测试车(Ego)车型为CICV_Car,初始车头方向偏离车道0°,以80km/h的速度在直道上定速行驶,得2分;<br/>'
            score += 2
        else:
            xml_score_detail = f'{item}.不满足测试车(Ego)车型为CICV_Car,初始车头方向偏离车道0°,以80km/h的速度在直道上定速行驶,不得分;<br/>'
        item += 1
        return score, xml_score_detail, weather_score, item
    except:
        return 0, '场景文件格式错误,场景搭建得0分;<br/>', weather_score, 1


if __name__ == '__main__':
    score = get_score('/home/tang/xml/test/real/acc_1.xml', Weather.SNOW)
    print(score)
