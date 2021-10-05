from . import *
from .heat_calculator import HeatCalculator
import datetime
import socket
import struct
import pytz
import re

#HOUR_ARCHIVE = 0x00
#DAY_ARCHIVE = 0x01
#MONTH_ARCHIVE = 0x02
tz = pytz.timezone('utc')

SIG = 0x55


class SA94HeatCalculator(HeatCalculator):

    __ip = ''
    __port = 0



    def __init__(self, ip, port, net_address):
        self.__ip = ip
        self.__port = port
        self.__net_address = net_address

    @staticmethod
    def __checksum(data):
        return bytes([0xFF - sum(list(bytearray(data)))&0xFF])

    @staticmethod
    def __bytes_to_int(data):
        return int.from_bytes(data, 'big')

    @staticmethod
    def __bytes_to_bcd(data):
        #print(data)
        return ((data[0] >> 4) & 0x0F) * 10 + (data[0] & 0x0F)

    @staticmethod
    def __bytes_to_float(data):
        #print(data.hex())
        return struct.unpack('>f', data)[0]

    @staticmethod
    def __aswega_bytes_to_float(data):
        b0 = data[0] - 0x2 if data[0] & 0xfe else 0
        b1 = data[1]
        b2 = data[2]
        b3 = data[3]
        x = [(b1 & 0x80) | (b0 >> 1 & 0x7f), ((b0 & 0x1) << 7) | (b1 & 0x7f), b2, b3]
        return struct.unpack('>f', bytes(x))[0]

    def getSettings(self, parameters):
        pass

    def __build_start_command(self):
        x = int(self.__net_address)
        x = 0xc00000 | ((x & 0xfc000) << 2) | ((x & 0x3f80) << 1) | (x & 0x7f)
        return x.to_bytes(3, 'big')

    def __connect_to_device(self):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        sock.send(self.__build_start_command())
        resp = sock.recv(1024)
        print(f'device status {resp.hex()}')
        return sock

    # def __unpack_archive_data(self, data, parameters):
    #
        # return x

    def getCurrentTime(self):
        sock = self.__connect_to_device()
        sock.send(0x8A.to_bytes(1, 'big'))
        resp = sock.recv(1024)
        hour = self.__bytes_to_bcd(resp[1:2])
        minute = self.__bytes_to_bcd(resp[2:3])
        second = self.__bytes_to_bcd(resp[3:4])
        sock.send(0x8B.to_bytes(1, 'big'))
        resp = sock.recv(1024)
        day = self.__bytes_to_bcd(resp[1:2])
        month = self.__bytes_to_bcd(resp[2:3])
        year = 2000 + self.__bytes_to_bcd(resp[3:4])
        sock.close()
        return datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    def getCurrentValues(self, parameters):
        data = {}
        sock = self.__connect_to_device()
        addresses = {
            'Q1': 0x80,
            'Q2': 0x81,
            'T1': 0x82,
            'T2': 0x83,
            'T3': 0x84,
            'dT': 0x85,
            'P': 0x86,
            'E': 0x87,
            'V1': 0x88,
            'V2': 0x89,
            'Tн': 0x8C, # Наработка
            'p1': 0x8E,
            'p2': 0x8F,
        }

        for parametr in parameters:
            sock.send(addresses[parametr].to_bytes(1, 'big'))
            resp = sock.recv(1024)
            data[parametr] = self.__aswega_bytes_to_float(resp)
        sock.close()
        return data

    def getHourArchives(self, parameters, from_dt, to_dt):
        resords = []
        sock = self.__connect_to_device()
        for s in (0xA200, 0xA300):
            for a in range(0x7f):
                message = (s|a).to_bytes(2,'big')
                sock.send(message)
                resp = sock.recv(1024)
                for n in range(0, 128, 32):
                    try:
                        data = resp[n:n+32]
                        rec = {'dt': None, 'Q1': None, 'Q2': None, 'T1': None, 'T2': None, 'T3': None, 'P': None}
                        if data[0] != 0xEE:
                            raise
                        day = self.__bytes_to_bcd(data[1:2])
                        month = self.__bytes_to_bcd(data[2:3])
                        year = 2000 + self.__bytes_to_bcd(data[3:4])
                        hour = self.__bytes_to_bcd(data[5:6])
                        minute = self.__bytes_to_bcd(data[6:7])
                        second = self.__bytes_to_bcd(data[7:8])
                        rec['dt'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
                        rec['Q1'] = self.__aswega_bytes_to_float(data[8:12]) if 'Q1' in parameters else None
                        rec['Q2'] = self.__aswega_bytes_to_float(data[12:16]) if 'Q2' in parameters else None
                        rec['T1'] = self.__aswega_bytes_to_float(data[16:20]) if 'T1' in parameters else None
                        rec['T2'] = self.__aswega_bytes_to_float(data[20:24]) if 'T2' in parameters else None
                        rec['T3'] = self.__aswega_bytes_to_float(data[24:28]) if 'T3' in parameters else None
                        rec['P'] = self.__aswega_bytes_to_float(data[28:32]) if 'P' in parameters else None


                        if rec['dt'] >= from_dt and rec['dt'] < to_dt:
                            resords.append(rec)
                    except Exception as e:
                        print(e)
        sock.send(b'0xff')
        sock.close()
        return resords

    def getDayArchives(self, parameters, from_dt, to_dt):
        resords = []
        sock = self.__connect_to_device()
        for s in (0xA400, 0xA500):
            for a in range(0x7f):
                message = (s|a).to_bytes(2,'big')
                sock.send(message)
                resp = sock.recv(1024)
                print(resp.hex())
                for n in range(0, 128, 32):
                    try:
                        data = resp[n:n+32]
                        rec = {'dt': None, 'Q1': None, 'Q2': None, 'T1': None, 'T2': None, 'T3': None, 'P': None}
                        if data[0] != 0xEE:
                            raise
                        day = self.__bytes_to_bcd(data[1:2])
                        month = self.__bytes_to_bcd(data[2:3])
                        year = 2000 + self.__bytes_to_bcd(data[3:4])

                        rec['dt'] = datetime.datetime(year=year, month=month, day=day)
                        rec['Tн'] = self.__aswega_bytes_to_float(data[4:8]) if 'Tн' in parameters else None
                        rec['Q1'] = self.__aswega_bytes_to_float(data[8:12]) if 'Q1' in parameters else None
                        rec['Q2'] = self.__aswega_bytes_to_float(data[12:16]) if 'Q2' in parameters else None
                        rec['T1'] = self.__aswega_bytes_to_float(data[16:20]) if 'T1' in parameters else None
                        rec['T2'] = self.__aswega_bytes_to_float(data[20:24]) if 'T2' in parameters else None
                        rec['T3'] = self.__aswega_bytes_to_float(data[24:28]) if 'T3' in parameters else None
                        rec['P'] = self.__aswega_bytes_to_float(data[28:32]) if 'P' in parameters else None
                        if rec['dt'] >= from_dt and rec['dt'] < to_dt:
                            resords.append(rec)
                    except Exception as e:
                        print(e)
                #if rec['dt'] >= to_dt
        sock.send(b'0xff')
        sock.close()
        return resords

    def getMonthArchives(self, parameters, from_dt, to_dt):
        raise
