import math
import xml.etree.ElementTree as ET

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
                    ego_car_type = des.attrib['Type']
                    for ego_init in player.iter('Init'):
                        for ego_data in ego_init:
                            if ego_data.tag == 'Speed':
                                ego_speed = float(ego_data.attrib['Value'])
                            elif ego_data.tag == 'PosAbsolute':
                                ego_direction = float(ego_data.attrib['Direction'])

                elif des.attrib['Name'] == 'veh_1':
                    veh_car_type = des.attrib['Type']
                    for veh_init in player.iter('Init'):
                        for veh_data in veh_init:
                            if veh_data.tag == 'Speed':
                                veh_speed = float(veh_data.attrib['Value'])
                            elif veh_data.tag == 'PosRelative':
                                if veh_data.attrib['Pivot'] == 'Ego':
                                    distance = float(veh_data.attrib['Distance'])
                                    veh_lane = int(veh_data.attrib['lane'])
        for player_actions in root.iter('PlayerActions'):
            if player_actions.attrib['Player'] == 'veh_1':
                for speed_change in player_actions.iter('SpeedChange'):
                    veh_acc_target = float(speed_change.attrib['Target'])
                for ttc_about in player_actions.iter('TTCRelative'):
                    ttc_pivot = ttc_about.attrib['Pivot']
                    ttc = float(ttc_about.attrib['TTC'])
                for lane_change in player_actions.iter('TTCRelative'):
                    veh_lane_change = int(lane_change.attrib['Direction'])

        if ego_speed == 80 / 3.6 and ego_direction == math.radians(0) and ego_car_type == 'CICV_Car':
            score += 1
            xml_score_detail = f'{item}.测试车(Ego)车型为CICV_Car,以80km/h,初始车头方向偏离车道0°,沿直道匀速行驶,且不驶出本车道,得1分;<br/>'
        else:
            xml_score_detail = f'{item}.不满足测试车(Ego)车型为CICV_Car,以80km/h,初始车头方向偏离车道0°,沿直道匀速行驶,且不驶出本车道,不得分;<br/>'
        item += 1
        if 20 / 3.6 <= veh_speed <= 30 / 3.6 and veh_lane == 1 and 100 <= distance <= 150 and ttc_pivot == 'Ego' and \
                ttc >= 3 and veh_lane_change == -1 and veh_acc_target == 0 and veh_car_type == 'Audi_A3_2009_red':
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.障碍车(veh_1)车型为Audi_A3_2009_blue,位于Ego车左侧车道的前方,与Ego车相距100-150m,且当TTC不小于3秒时,障碍车以20-30km/h的初速度,开始变道切入自车前方,减速至静止,得1分;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.不满足障碍车(veh_1)车型为Audi_A3_2009_blue,位于Ego车左侧车道的前方,与Ego车相距100-150m,且当TTC不小于3秒时,障碍车以20-30km/h的初速度,开始变道切入自车前方,减速至静止,不得分;<br/>'
        item += 1
        return score, xml_score_detail, weather_score, item
    except:
        return 0, '场景文件格式错误，场景搭建得0分;<br/>', weather_score, 1


if __name__ == '__main__':
    score = get_score('/home/tang/xml/pro/real/aeblka_5.xml', Weather.RAIN)
    print(score)
