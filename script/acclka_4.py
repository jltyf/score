import math
import xml.etree.ElementTree as ET

from button_tool.py.vtdTools import Weather


def get_score(xml_path, weather_result):
    ego_car_type = None
    veh_car_type = None
    ego_speed = 500
    ego_direction = 500
    veh_speed = 500
    veh_start_x = 10000
    veh_start_y = 10000
    veh_acc = 500
    veh_acc_target = 500
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
                elif des.attrib['Name'] == 'veh_1':
                    veh_car_type = des.attrib['Type']
                    for veh_init in player.iter('Init'):
                        for veh_data in veh_init:
                            if veh_data.tag == 'Speed':
                                veh_speed = float(veh_data.attrib['Value'])
                            elif veh_data.tag == 'PosAbsolute':
                                veh_start_x = float(veh_data.attrib['X'])
                                veh_start_y = float(veh_data.attrib['Y'])
        for player_actions in root.iter('PlayerActions'):
            if player_actions.attrib['Player'] == 'veh_1':
                for speed_change in player_actions.iter('SpeedChange'):
                    veh_acc = float(speed_change.attrib['Rate'])
                    veh_acc_target = float(speed_change.attrib['Target'])

        if ego_speed == 80 / 3.6 and ego_direction == math.radians(5) and ego_car_type == 'CICV_Car':
            score += 1
            xml_score_detail = f'{item}.?????????(Ego)?????????CICV_Car,???80km/h,??????????????????????????????5??,??????????????????,?????????????????????,???1???;<br/>'
        else:
            xml_score_detail = f'{item}.??????????????????(Ego)?????????CICV_Car,???80km/h,??????????????????????????????5??,??????????????????,?????????????????????,?????????;<br/>'
        item += 1
        if 19.99 / 3.6 <= veh_speed <= 70.01 / 3.6 and 1129.64 <= veh_start_x <= 1131.59 and 175 <= veh_start_y <= 225 \
                and veh_acc <= 6 and veh_acc_target == 10 / 3.6 and veh_car_type == 'Audi_A3_2009_red':
            score += 1
            xml_score_detail = xml_score_detail + f'{item}.?????????(veh_1)?????????Audi_A3_2009_red,??????Ego??????????????????50-100m??????????????????,????????????20-70km/h,??????????????????6m/s2,?????????10km/h,???1???;<br/>'
        else:
            xml_score_detail = xml_score_detail + f'{item}.??????????????????(veh_1)?????????Audi_A3_2009_red,??????Ego??????????????????50-100m??????????????????,????????????20-70km/h,??????????????????6m/s2,?????????10km/h,?????????;<br/>'
        item += 1
        return score, xml_score_detail, weather_score, item
    except:
        return 0, '??????????????????????????????????????????0???;<br/>', weather_score, 1


if __name__ == '__main__':
    score = get_score('/home/tang/xml/pro/real/acclka_4.xml', Weather.RAIN)
    print(score)
