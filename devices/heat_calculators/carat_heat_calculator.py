from . import *
from .heat_calculator import HeatCalculator
import datetime
import socket
import struct
from heatcontrol.devices.heat_calculators.heat_calculator import UnknownParametrName


HOUR_ARCHIVE = 0x00
DAY_ARCHIVE = 0x10
MONTH_ARCHIVE = 0x20

class Carat307HeatCalculator(HeatCalculator):

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
        return int.from_bytes(data, 'little')

    @staticmethod
    def __hours_to_float(data):
        return Carat307HeatCalculator.__bytes_to_int(data)/60

    @staticmethod
    def __bytes_to_float(data):
        return struct.unpack('<f', data)[0]

    def getSettings(self, parameters):
        pass

    def getCurrentTime(self):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        request_number = 0x0
        message = [self.__net_address, 0x03, 0x00, 0x62, 0x00, 0x01, ]
        message = bytes(message)
        message += self.__crc16(message)
        sock.send(message)
        recv = sock.recv(1024)
        return datetime.datetime(year=self.__bytes_to_int(recv[9:11]), month=recv[8], day=recv[6],
            hour=recv[5], minute=recv[4], second=recv[3])
        sock.close()

    def __get_params(self):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        message = [self.__net_address, 0x03, 0x01, 0x06, 0x00, 0x038, ]
        message = bytes(message)
        message += self.__crc16(message)
        sock.send(message)
        r = sock.recv(1024)
        sock.close()
        params = []
        for b in r[4:]:
            if 0xff == b:
                break
            if 0xC0 == b:
                params.append(('NS',self.__bytes_to_int))
            elif 0xD1 == b:
                params.append(('Tmin', self.__hours_to_float) )
            elif 0xD2 == b:
                params.append(('Tmax',self. __hours_to_float))
            elif 0xD3 == b:
                params.append(('Tdt', self.__hours_to_float))
            elif 0xD4 == b:
                params.append(('Tф', self.__hours_to_float))
            elif 0xD5 == b:
                params.append(('Tэп', self.__hours_to_float))
            elif 0xB0 == b:
                params.append(('Наработка', self.__hours_to_float))
            elif 0x50 == b & 0x50:
                params.append(('Q{}'.format(b & 0xF), self.__bytes_to_float))
            elif 0x40 == b & 0x40:
                params.append(('P{}'.format(b & 0xF), self.__bytes_to_float))
            elif 0x30 == b & 0x30:
                params.append(('T{}'.format(b & 0xF), self.__bytes_to_float))
            elif 0x20 == b & 0x20:
                params.append(('G{}'.format(b & 0xF), self.__bytes_to_float))
            elif 0x10 == b & 0x10:
                params.append(('V{}'.format(b & 0x0F), self.__bytes_to_float))

        return params

    def getCurrentValues(self, parameters):
        params = self.__get_params()
        for parameter in parameters:
            if parameter not in [param[0] for param in params]:
                raise UnknownParametrName('Unknown parameter \'{}\''.format(parameter))
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        message = [self.__net_address, 0x03, 0x20, 0x00, 0x00, 0x038, ]
        message = bytes(message)
        message += self.__crc16(message)

        sock.send(message)
        r = sock.recv(1024)
        sock.close()

        result = {}
        offset = 3 # initial offset
        for i,param in enumerate(params):
            if param[0] in parameters:
                result[param[0]]  = param[1](r[offset + i*4:offset + i*4 + 4])
        return result

    def __getArchives(self, archive_type, parameters, from_dt, to_dt):
        params = self.__get_params()
        for parameter in parameters:
            if parameter not in [param[0] for param in params]:
                raise UnknownParametrName('Unknown parameter \'{}\''.format(parameter))
        report_date = from_dt
        result = []
        offset = 21 # initial offset
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        d = report_date.day
        m = report_date.month
        y = report_date.year - 2000
        h = report_date.hour
        message = [self.__net_address, 0x10, 0x00, 0x60, 0x00, 0x02, 0x04, h, d, m, y]
        message = bytes(message)
        message += self.__crc16(message)
        sock.send(message)
        r = sock.recv(1024)
        message = [self.__net_address, 0x03, 0x00, archive_type, 0x00, 0x78]
        message = bytes(message)
        message += self.__crc16(message)
        sock.send(message)
        r = sock.recv(1024)
        report_date = datetime.datetime(year=r[20]+2000, month=r[19], day=r[18], hour=r[17], minute=r[16])
        while(report_date <= to_dt):
            result_record = {'datetime': report_date}
            for i,param in enumerate(params):
                if param[0] in parameters:
                    result_record[param[0]]  = param[1](r[offset + i*4:offset + i*4 + 4])
            result.append(result_record)
            message = [self.__net_address, 0x03, 0x00, archive_type + 0x05, 0x00, 0x78]
            message = bytes(message)
            message += self.__crc16(message)
            sock.send(message)
            r = sock.recv(1024)
            report_date = datetime.datetime(year=r[20]+2000, month=r[19], day=r[18], hour=r[17], minute=r[16])
        sock.close()
        return result

    def getHourArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(HOUR_ARCHIVE, parameters, from_dt, to_dt )

    def getDayArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(DAY_ARCHIVE, parameters, from_dt, to_dt )


    def getMonthArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(MONTH_ARCHIVE, parameters, from_dt, to_dt )
