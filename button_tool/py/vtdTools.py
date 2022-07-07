# coding = iso8859-1

import enum
import os
import socket
import struct
import subprocess
import xml.etree.ElementTree as ET
from threading import Thread
from time import sleep


def getSensorName(sensorInfo):
    try:
        Sensor = ET.XML(sensorInfo)
        if Sensor.tag == "Sensor":
            return Sensor.attrib["name"]

    except ET.ParseError as e:
        # it happens when VTD sends invalid xml-format scp msg
        # print("VTD sucks:", e)
        pass


class Weather(enum.Enum):
    DEFAULT = "default"
    RAIN = "rain"
    SNOW = "snow"
    DRY = "none"


def stopAlgorithm():
    """
    stop algorithm
    :return:
    """
    cmd = "ps aux | egrep 'rosrun|roslaunch|rosrun|rosout|\.ros' | awk '{print $2}' | xargs kill -9"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(1)
    process.kill()
    process.wait()


def startAlgorithm(workingDir, scriptPath):
    """
    start algorithm
    :param workingDir:
    :param scriptPath: algorithm start script
    :return:
    """
    origWD = os.getcwd()
    os.chdir(workingDir)
    process = subprocess.Popen(scriptPath, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(2)
    os.chdir(origWD)
    process.kill()
    process.wait()


def stopRosVtdConnector():
    """
    stop ros-vtd connector
    :return:
    """
    cmd = "ps aux | egrep 'vtdToRos|rosToVtd|roscore|rosmaster' | awk '{print $2}' | xargs kill -9"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(1)
    process.kill()
    process.wait()


def startRosVtdConnector(workingDir, scriptPath):
    """
    start ros-vtd connector
    :param workingDir:
    :param scriptPath: connector start script path
    :return:
    """
    origWD = os.getcwd()
    os.chdir(workingDir)
    process = subprocess.Popen(scriptPath, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(2)
    os.chdir(origWD)
    process.kill()
    process.wait()


def detectWeatherChange(scpMsg):
    """
    parse scp msg, try to find required attribute value
    :param scpMsg: xml-format msg
    :return: weather
    """

    # scp msg sample ↓
    # <Environment>
    #   <Friction value="1.000000" />
    #   <Date day="1" month="6" year="2008" />
    #   <TimeOfDay headlights="true" timezone="0" value="61200" />
    #   <Sky cloudState="6/8" visibility="11919.190430" />
    #   <Precipitation intensity="0.500000" type="rain" />
    #   <Road effectScale="0.500000" state="dry" />
    # </Environment>

    try:
        Environment = ET.XML(scpMsg)
        if Environment.tag == "Environment":
            print("\r", end="")
            # print(scpMsg)
            Precipitation = Environment.find("Precipitation")
            if Precipitation is not None:
                weather = Precipitation.attrib["type"]
                print(weather)
                if weather == "rain":
                    return Weather.RAIN
                elif weather == "snow":
                    return Weather.SNOW
                elif weather == "none":
                    return Weather.DRY

    except ET.ParseError as e:
        # it happens when VTD sends invalid xml-format scp msg
        # print("VTD sucks:", e)
        pass


def sendScpMsg(sock, scpMsg):
    """
    make a tcp connection first, then send a scp msg
    :param sock: sockFD
    :param scpMsg: scp msg content
    :return:
    """
    scpMsgLen = len(scpMsg)
    scpMsgFmt = "@" + str(scpMsgLen) + "s"

    magicNo = struct.pack("@H", 40108)  # 2 bytes
    version = struct.pack("@H", 0x0001)  # 2 bytes
    sender = struct.pack("@64s", "goClient".encode("utf-8"))  # 64 bytes
    receiver = struct.pack("@64s", "any".encode("utf-8"))  # 64 bytes
    dataSize = struct.pack("@I", scpMsgLen)  # 4 bytes
    scpData = struct.pack(scpMsgFmt, scpMsg.encode("utf-8"))  # 28 bytes

    data = magicNo + version + sender + receiver + dataSize + scpData
    sock.sendall(data)


def recvScpMsg(targetIP, targetPort, terminated):
    """
    make tcp-conn with VTD, keep receiving scp msg and examine its content
    :param targetIP: VTD IP
    :param targetPort: VTD port
    :param terminated: termination flag
    :return:
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((targetIP, targetPort))
        socket.setdefaulttimeout(5)
        sensorsInfoDict = {}

        print("Weather Detector Connected")

        latestWeather = Weather.DEFAULT

        numDot = 0
        while not terminated[0]:

            try:
                recvData = sock.recv(4096)
            except socket.timeout as e:
                continue

            scpMsgLen = len(recvData) - 136
            dataFmt = "@HH64s64sI" + str(scpMsgLen) + "s"

            try:
                _, _, _, _, _, rawScpMsg = struct.unpack(dataFmt, recvData)
                scpMsg = rawScpMsg[:-1].decode("iso8859-1")
                # print(scpMsg)

                tempWeather = detectWeatherChange(scpMsg)
                if tempWeather is not None:
                    latestWeather = tempWeather

                # extract sensor info from scp msg
                tempSensorsInfoList = detectSensor(scpMsg)
                if tempSensorsInfoList:

                    # store updated sensor info in local dict
                    # print("\nupdate, len =", len(tempSensorsInfoList))
                    for si in tempSensorsInfoList:
                        sensorsInfoDict[getSensorName(si)] = si
                        # print(getSensorName(si))

                    # print all current sensor info
                    # print("total, len =", len(sensorsInfoDict))
                    # for k in sensorsInfoDict.keys():
                    #     print(sensorsInfoDict[k])


            except UnicodeDecodeError as e:
                # it happens when scp msg contains invalid character
                # print("VTD screwed up:", e)
                pass

            except struct.error as e:
                # it happens when VTD re-enters config mode, start reconnection process
                # print("\rWeather Detector Disconnected")
                sock.close()
                sleep(1)
                newSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                newSock.connect((targetIP, targetPort))
                sock = newSock
                # print("\rWeather Detector Reconnected ")

        print("\r                 ", end="\r")
        sock.close()
        return latestWeather, sensorsInfoDict


class WeatherDetector(Thread):
    """
    examine real-time weather change from VTD UI, return result when needed
    """

    def __init__(self, targetIP, targetPort):
        Thread.__init__(self)
        self.latestSensorsInfo = []
        self.targetIP = targetIP
        self.targetPort = targetPort
        self.terminated = [False]
        self.latestWeather = Weather.DEFAULT

    def run(self):
        """
        start a new thread to do the weather examination task
        :return:
        """
        self.latestWeather, self.latestSensorsInfo = recvScpMsg(self.targetIP, self.targetPort, self.terminated)

    def stop(self):
        """
        update termination flag
        :return:
        """
        self.terminated[0] = True

    def getResult(self):
        """
        examine the weather info and return the result
        :return: True if weather-exam is passed, False otherwise
        """
        return self.latestWeather


def stopVtd(scriptPath):
    """
    stop VTD
    :param scriptPath: VTD stop script path
    :return:
    """
    process = subprocess.Popen(scriptPath, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(1)
    process.kill()
    process.wait()


def detectSensor(scpMsg):
    """
    parse scp msg, try to find required attribute value
    :param scpMsg: xml-format msg
    :return: list of sensors' setup
    """
    # scp msg sample ↓
    #
    # <Sensor name="sensor_1" ... ></ Sensor>
    # <Sensor name="sensor_2" ... ></ Sensor>!@#$$%^<Sensor name="sensor_3" ... ></ Sensor>
    #
    # <Sensor name="Sensor_USK_1" type="video" >
    #   <Player name="Ego"/>
    #   <Frustum near="0.000000" far="100.000000" left="60.000000" right="60.000000" bottom="22.500000" top="22.500000" />
    #   <Position dx="1.500000" dy="0.000000" dz="1.700000" dhDeg="0.000000" dpDeg="0.000000" drDeg="0.000000" />
    #   <Origin type="usk" /> <Cull maxObjects="10" enable="true" />
    #   <Filter objectType="none" />
    #   <Filter objectType="vehicle" />
    #   <Filter objectType="pedestrian" />
    #   <Filter objectType="light" />
    #   <Filter objectType="trafficSign" />
    #   <Filter objectType="laneInfo" />
    #   <Filter objectType="roadMarks" />
    # </Sensor>

    detectedSensorsInfo = []

    if scpMsg[:13] == "<Sensor name=":

        firstSensorEndIndex = scpMsg.find("</Sensor>") + 9
        firstSensorInfo = scpMsg[:firstSensorEndIndex]
        detectedSensorsInfo.append(firstSensorInfo)

        restScp = scpMsg[firstSensorEndIndex:]
        if restScp and restScp!=' ':
            secondSensorBeginIndex = restScp.find("<Sensor name=")
            if secondSensorBeginIndex>=0:
                secondSensorEndIndex = restScp.find("</Sensor>") + 9
                secondSensorInfo = restScp[secondSensorBeginIndex:secondSensorEndIndex]
                detectedSensorsInfo.append(secondSensorInfo)

    return detectedSensorsInfo


def startVtd(scriptPath):
    """
    start VTD
    :param scriptPath: VTD start script path
    :return:
    """
    # addCmd = " --setup=EY_CloudSimulation --project=EY_CloudSimulation"
    process = subprocess.Popen(scriptPath + ' --setup=NationalCompetition --project=NationalCompetition',
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    sleep(1)
    process.kill()
    process.wait()
    sleep(4)  # wait Vtd to fully start


def exitGracefully(signum, frame):
    """
    stop all relative process then exit
    :param signum:
    :param frame:
    :return:
    """
    # stopVtd(vtdStopScript)
    stopAlgorithm()
    stopRosVtdConnector()
    print("Termination:", signum, frame)
    exit(0)
