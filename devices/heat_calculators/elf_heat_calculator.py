from . import *
from .heat_calculator import HeatCalculator
import datetime
import socket
import struct


CURRENT_VALUES = 0x09
HOUR_ARCHIVE = 0x1a
DAY_ARCHIVE = 0x1b
MONTH_ARCHIVE = 0x1c


# Описание параметров:
#  Er1 код ошибок подсистемы 1
#  H1 наработка подистемы 1
#  Q1_под тепловая энергия подающего трубопровода
#  Q1_обр тепловая энергия обратного трубопровода
#  V1_под объем или масса подающего трубопровода
#  V1_обр объем или масса обратного трубопровода
#  T1_под температура подающего трубопровода
#  T1_обр температура обратного трубопровода
#  P1_под давление подающего трубопровода
#  P1_обр давление обратного трубопровода
#
# И также для каждой из 6 подсистем.

class Elf04HeatCalculator(HeatCalculator):

    __ip = ''
    __port = 0
    __net_address = 0x0



    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port
        self. __net_address = 0x01

    @staticmethod
    def __crc16(data):
        crc = 0xFFFF
        l = len(data)
        i = 0
        for x in range(0, l):
            crc = int(crc/256)*256 + crc%256^data[x]
            for y in range(0, 8):
                if crc & 0x1:
                    crc = (crc >> 1) ^ 0xa001;
                else:
                    crc>>=1;
        return crc.to_bytes(2, 'little')

    @staticmethod
    def __bytes_to_int(data):
        return int.from_bytes(data, 'big')

    @staticmethod
    def __bytes_to_float(data):
        return struct.unpack('>f', data[2:4] + data[0:2])[0]

    @staticmethod
    def __bytes_to_double(data):
        return struct.unpack('>d', data[6:8] + data[4:6] + data[2:4] + data[0:2])[0]

    def getSettings(self, parameters):
        pass


    def getCurrentTime(self):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        message = bytes([self.__net_address, 0x04, 0x00, 0x00, 0x00, 0x03])
        message += self.__crc16(message)
        sock.send(message)
        recv = sock.recv(1024)
        return datetime.datetime(year=2000+recv[3], month=recv[4], day=recv[5],
            hour=recv[6], minute=recv[7], second=recv[8]&0x7f)
        sock.close()


    def getCurrentValues(self, parameters):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        message = bytes([
            self.__net_address, 0x10, 0x00, 0x00, 0x00, 0x07, 0x0e, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, CURRENT_VALUES, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00
        ])
        message += self.__crc16(message)
        sock.send(message)
        sock.recv(1024)
        message = bytes([self.__net_address, 0x04, 0x01, 0x00, 0x00, 0x7a])
        message += self.__crc16(message)
        sock.send(message)
        r = sock.recv(1024)
        result = {}
        for subsystem in range(6):
            if 'Er{}'.format(subsystem + 1) in parameters:
                result['Er{}'.format(subsystem + 1)] = self.__bytes_to_int(r[7 + 40*subsystem:11 + 40*subsystem])
            if 'H{}'.format(subsystem + 1) in parameters:
                result['H{}'.format(subsystem + 1)]= self.__bytes_to_float(r[11 + 40*subsystem:15 + 40*subsystem])
            if 'Q{}_под'.format(subsystem + 1) in parameters:
                result['Q{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[15 + 40*subsystem:19 + 40*subsystem])
            if 'Q{}_обр'.format(subsystem + 1) in parameters:
                result['Q{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[19 + 40*subsystem:23 + 40*subsystem])
            if 'V{}_под'.format(subsystem + 1) in parameters:
                result['V{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[23 + 40*subsystem:27 + 40*subsystem])
            if 'V{}_обр'.format(subsystem + 1) in parameters:
                result['V{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[27 + 40*subsystem:31 + 40*subsystem])
            if 'T{}_под'.format(subsystem + 1) in parameters:
                result['T{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[31 + 40*subsystem:35 + 40*subsystem])
            if 'T{}_обр'.format(subsystem + 1) in parameters:
                result['T{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[35 + 40*subsystem:39 + 40*subsystem])
            if 'P{}_под'.format(subsystem + 1) in parameters:
                result['P{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[39 + 40*subsystem:43 + 40*subsystem])
            if 'P{}_обр'.format(subsystem + 1) in parameters:
                result['P{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[43 + 40*subsystem:47 + 40*subsystem])
        sock.close()
        return result

    def __getArchives(self, archive_type, parameters, from_dt, to_dt):
        report_date = from_dt
        result = []
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        while(report_date <= to_dt):
            d = report_date.day
            m = report_date.month
            y = report_date.year - 2000
            h = report_date.hour
            if HOUR_ARCHIVE == archive_type:
                report_date += datetime.timedelta(hours=1)
            if DAY_ARCHIVE == archive_type:
                report_date += datetime.timedelta(days=1)
            if MONTH_ARCHIVE == archive_type:
                report_date = (report_date.replace(day=1) + datetime.timedelta(days=31)).replace(day=1)

            message = bytes([
                self.__net_address, 0x10, 0x00, 0x00, 0x00, 0x07, 0x0e, y, m, d,
                h, 0x00, 0x00, 0x00, archive_type, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00
            ])
            message += self.__crc16(message)
            sock.send(message)
            sock.recv(1024)
            message = bytes([self.__net_address, 0x04, 0x01, 0x00, 0x00, 0x7a])
            message += self.__crc16(message)
            sock.send(message)
            r = sock.recv(1024)
            result_record = {'datetime': datetime.datetime(year=r[3]+2000, month=r[4], day=r[5], hour=r[6])}
            for subsystem in range(6):
                if 'Er{}'.format(subsystem + 1) in parameters:
                    result_record['Er{}'.format(subsystem + 1)] = self.__bytes_to_int(r[7 + 40*subsystem:11 + 40*subsystem])
                if 'H{}'.format(subsystem + 1) in parameters:
                    result_record['H{}'.format(subsystem + 1)]= self.__bytes_to_float(r[11 + 40*subsystem:15 + 40*subsystem])
                if 'Q{}_под'.format(subsystem + 1) in parameters:
                    result_record['Q{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[15 + 40*subsystem:19 + 40*subsystem])
                if 'Q{}_обр'.format(subsystem + 1) in parameters:
                    result_record['Q{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[19 + 40*subsystem:23 + 40*subsystem])
                if 'V{}_под'.format(subsystem + 1) in parameters:
                    result_record['V{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[23 + 40*subsystem:27 + 40*subsystem])
                if 'V{}_обр'.format(subsystem + 1) in parameters:
                    result_record['V{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[27 + 40*subsystem:31 + 40*subsystem])
                if 'T{}_под'.format(subsystem + 1) in parameters:
                    result_record['T{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[31 + 40*subsystem:35 + 40*subsystem])
                if 'T{}_обр'.format(subsystem + 1) in parameters:
                    result_record['T{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[35 + 40*subsystem:39 + 40*subsystem])
                if 'P{}_под'.format(subsystem + 1) in parameters:
                    result_record['P{}_под'.format(subsystem + 1)] = self.__bytes_to_float(r[39 + 40*subsystem:43 + 40*subsystem])
                if 'P{}_обр'.format(subsystem + 1) in parameters:
                    result_record['P{}_обр'.format(subsystem + 1)] = self.__bytes_to_float(r[43 + 40*subsystem:47 + 40*subsystem])
            result.append(result_record)
        sock.close()
        return result

    def getHourArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(HOUR_ARCHIVE, parameters, from_dt, to_dt )

    def getDayArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(DAY_ARCHIVE, parameters, from_dt, to_dt )


    def getMonthArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(MONTH_ARCHIVE, parameters, from_dt, to_dt )
