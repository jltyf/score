# coding = iso8859-1

import socket
import struct
import threading
import xml.etree.ElementTree as ET


def detectWeatherChange(scpMsg):
    """
    parse scp msg, try to find required attribute value
    :param scpMsg: xml-format msg
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
            print(scpMsg)
            Precipitation = Environment.find("Precipitation")
            if Precipitation is not None:
                if Precipitation.attrib["type"] == "rain":
                    print("Good")
                else:
                    print("Bad")

    except ET.ParseError as e:
        print("VTD sucks:", e)


def recvScpMsg(targetIP, targetPort):
    """
    make tcp-conn with VTD, keep receiving scp msg and examine its content
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((targetIP, targetPort))

        numDot = 0
        weatherChanged = False
        while not weatherChanged:

            recvData = sock.recv(4096)
            scpMsgLen = len(recvData) - 136
            dataFmt = "@HH64s64sI" + str(scpMsgLen) + "s"

            try:
                _, _, _, _, _, rawScpMsg = struct.unpack(dataFmt, recvData)
                scpMsg = rawScpMsg[:-1].decode("iso8859-1")
                # print(scpMsg)

                # ↓ the following block of code is pure useless, just for fun ↓
                dots = ""
                for _ in range(int(numDot / 2)):
                    dots += ". "
                numDot += 1
                if numDot > 7:
                    numDot = 0
                print("                 ", end="")
                print("\rReceiving scp msg " + dots, end="")
                # ↑ useless code ends here ↑

                detectWeatherChange(scpMsg)

            except UnicodeDecodeError as e:
                print("VTD screwed up:", e)


if __name__ == "__main__":
    tServer = threading.Thread(target=recvScpMsg, args=("127.0.0.1", 48179))
    tServer.start()
    tServer.join()
