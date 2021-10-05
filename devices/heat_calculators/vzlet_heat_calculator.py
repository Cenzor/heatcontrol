from . import *
from .heat_calculator import HeatCalculator
import datetime
import socket
import struct
import pytz
from heatcontrol.devices.heat_calculators.heat_calculator import UnknownParametrName

HOUR_ARCHIVE = 0x00
DAY_ARCHIVE = 0x01
MONTH_ARCHIVE = 0x02
tz = pytz.timezone('utc')

class TSRV043HeatCalculator(HeatCalculator):

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
    def __bytes_to_timestamp(data):
        epoch = int.from_bytes(data, 'big')
        return datetime.datetime.fromtimestamp(epoch,  tz=tz)

    @staticmethod
    def __bytes_to_int(data):
        return int.from_bytes(data, 'big')

    @staticmethod
    def __bytes_to_temperature(data):
        return TSRV043HeatCalculator.__bytes_to_int(data)*0.001

    @staticmethod
    def __bytes_to_pressure(data):
        return TSRV043HeatCalculator.__bytes_to_int(data)*0.0001

    @staticmethod
    def __bytes_to_hours(data):
        return TSRV043HeatCalculator.__bytes_to_int(data)/60

    def getSettings(self, parameters):
        pass

    def getCurrentTime(self):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        message = [self.__net_address, 0x03, 0x80, 0x04, 0x00, 0x02,]
        message = bytes(message)
        message += self.__crc16(message)
        sock.send(message)
        recv = sock.recv(1024)
        sock.close()
        return self.__bytes_to_timestamp(recv[3:7])


    def getCurrentValues(self, parameters):
        raise

    def __getArchiveByDate(self, archive_type, parameters, from_dt, to_dt):
        sock = socket.socket()
        sock.connect((self.__ip, self.__port))
        sock.settimeout(20)
        report_date = from_dt
        result = []
        while(report_date <= to_dt):
            d = report_date.day
            m = report_date.month
            y = report_date.year - 2000
            h = report_date.hour
            mi = report_date.minute
            s = report_date.second
            time_field_size = 1 if HOUR_ARCHIVE == archive_type else 2
            if HOUR_ARCHIVE == archive_type:
                report_date += datetime.timedelta(hours=1)
            if DAY_ARCHIVE == archive_type:
                report_date += datetime.timedelta(days=1)
            if MONTH_ARCHIVE == archive_type:
                report_date = (report_date.replace(day=1) + datetime.timedelta(days=31)).replace(day=1)
            message = [self.__net_address, 0x41, 0x00, HOUR_ARCHIVE, 0x00, 0x01, 0x01, s, mi, h, d, m, y]
            message = bytes(message)
            message += self.__crc16(message)
            sock.send(message)
            r = sock.recv(1024)
            #print(r.hex())
            result_record = {}
            io = 3 #initial offset
            offsets = {
                'datetime' : (io, io+4, self.__bytes_to_timestamp),
                'indx': (io+4, io+6, self.__bytes_to_int),
                'Tраб': (io+6, io+10, lambda x: self.__bytes_to_int(x)/3600),
                'V1': (io+10, io+14, self.__bytes_to_int),
                'V2': (io+14, io+18, self.__bytes_to_int),
                'V3': (io+18, io+22, self.__bytes_to_int),
                'V4': (io+22, io+26, self.__bytes_to_int),
                'V5': (io+26, io+30, self.__bytes_to_int),
                'V6': (io+30, io+34, self.__bytes_to_int),
                'M1': (io+34, io+38, self.__bytes_to_int),
                'M2': (io+38, io+42, self.__bytes_to_int),
                'M3': (io+42, io+46, self.__bytes_to_int),
                'M4': (io+46, io+50, self.__bytes_to_int),
                'M5': (io+50, io+54, self.__bytes_to_int),
                'M6': (io+54, io+58, self.__bytes_to_int),
                'Mтс1': (io+58, io+62, self.__bytes_to_int),
                'Mтс2': (io+62, io+66, self.__bytes_to_int),
                'Mтс3': (io+66, io+70, self.__bytes_to_int),
                'Mсум': (io+70, io+74, self.__bytes_to_int),
                'Qтс1': (io+74, io+78, self.__bytes_to_int),
                'Qтс2': (io+78, io+82, self.__bytes_to_int),
                'Qтс3': (io+82, io+86, self.__bytes_to_int),
                'Qсум': (io+86, io+90, self.__bytes_to_int),
                't1': (io+90, io+92, self.__bytes_to_temperature),
                't2': (io+92, io+94, self.__bytes_to_temperature),
                't3': (io+94, io+96, self.__bytes_to_temperature),
                't4': (io+96, io+98, self.__bytes_to_temperature),
                't5': (io+98, io+100, self.__bytes_to_temperature),
                'tхв': (io+100, io+102, self.__bytes_to_temperature),
                'P1': (io+102, io+104, self.__bytes_to_pressure),
                'P2': (io+104, io+106, self.__bytes_to_pressure),
                'P3': (io+106, io+108, self.__bytes_to_pressure),
                'P4': (io+108, io+110, self.__bytes_to_pressure),
                'Pхв': (io+110, io+112, self.__bytes_to_pressure),
                'Tпит': (io + 112 + 0*time_field_size , io + 112 + 1*time_field_size, self.__bytes_to_hours),
                'Tакт5': (io + 112 + 1*time_field_size , io + 112 + 2*time_field_size, self.__bytes_to_hours),
                'Tакт6': (io + 112 + 2*time_field_size , io + 112 + 3*time_field_size, self.__bytes_to_hours),
                'Tотк1': (io + 112 + 3*time_field_size , io + 112 + 4*time_field_size, self.__bytes_to_hours),
                'Tотк2': (io + 112 + 4*time_field_size , io + 112 + 5*time_field_size, self.__bytes_to_hours),
                'Tотк3': (io + 112 + 5*time_field_size , io + 112 + 6*time_field_size, self.__bytes_to_hours),
                'Tоткс': (io + 112 + 6*time_field_size , io + 112 + 7*time_field_size, self.__bytes_to_hours),
                'Tнс1': (io + 112 + 7*time_field_size , io + 112 + 8*time_field_size, self.__bytes_to_hours),
                'Tнс2': (io + 112 + 8*time_field_size , io + 112 + 9*time_field_size, self.__bytes_to_hours),
                'Tнс3': (io + 112 + 9*time_field_size , io + 112 + 10*time_field_size, self.__bytes_to_hours),
                'Tнс4': (io + 112 + 10*time_field_size , io + 112 + 11*time_field_size, self.__bytes_to_hours),
                'Tнс5': (io + 112 + 11*time_field_size , io + 112 + 12*time_field_size, self.__bytes_to_hours),
                'Tнс6': (io + 112 + 12*time_field_size , io + 112 + 13*time_field_size, self.__bytes_to_hours),
                'Tнс7': (io + 112 + 13*time_field_size , io + 112 + 14*time_field_size, self.__bytes_to_hours),
                'Tнс8': (io + 112 + 14*time_field_size , io + 112 + 15*time_field_size, self.__bytes_to_hours),
                'Tнс9': (io + 112 + 15*time_field_size , io + 112 + 16*time_field_size, self.__bytes_to_hours),
                'Tнс10': (io + 112 + 16*time_field_size , io + 112 + 17*time_field_size, self.__bytes_to_hours),
                'Tнс11': (io + 112 + 17*time_field_size , io + 112 + 18*time_field_size, self.__bytes_to_hours),
                'Tнс12': (io + 112 + 18*time_field_size , io + 112 + 19*time_field_size, self.__bytes_to_hours),
                'Tнс13': (io + 112 + 19*time_field_size , io + 112 + 20*time_field_size, self.__bytes_to_hours),
                'Tнс14': (io + 112 + 20*time_field_size , io + 112 + 21*time_field_size, self.__bytes_to_hours),
                'Tнс15': (io + 112 + 21*time_field_size , io + 112 + 22*time_field_size, self.__bytes_to_hours),
                'Tнс16': (io + 112 + 22*time_field_size , io + 112 + 23*time_field_size, self.__bytes_to_hours),
                'Tнс17': (io + 112 + 23*time_field_size , io + 112 + 24*time_field_size, self.__bytes_to_hours),
                'Tнс18': (io + 112 + 24*time_field_size , io + 112 + 25*time_field_size, self.__bytes_to_hours),
                'Tнс19': (io + 112 + 25*time_field_size , io + 112 + 26*time_field_size, self.__bytes_to_hours),
                'Tнс20': (io + 112 + 26*time_field_size , io + 112 + 27*time_field_size, self.__bytes_to_hours),
                'Tнс21': (io + 112 + 27*time_field_size , io + 112 + 28*time_field_size, self.__bytes_to_hours),
                'Tнс22': (io + 112 + 28*time_field_size , io + 112 + 29*time_field_size, self.__bytes_to_hours),
                'Стат': (io + 112 + 29*time_field_size, io + 112 + 29*time_field_size + 1, self.__bytes_to_int),
                'Статизм': (io + 112 + 29*time_field_size + 1, io + 112 + 29*time_field_size + 2, self.__bytes_to_int),
            }
            #print(offsets)
            for parameter in parameters:
                if parameter in offsets.keys():
                    d = r[offsets[parameter][0]:offsets[parameter][1]]
                    result_record[parameter] = offsets[parameter][2](d)
                else:
                    raise UnknownParametrName('Unknown parameter \'{}\''.format(parameter))
            result.append(result_record)
        sock.close()
        return result

    def getHourArchives(self, parameters, from_dt, to_dt):
        return self.__getArchiveByDate(HOUR_ARCHIVE, parameters, from_dt, to_dt )

    def getDayArchives(self, parameters, from_dt, to_dt):
        return self.__getArchiveByDate(DAY_ARCHIVE, parameters, from_dt, to_dt )

    def getMonthArchives(self, parameters, from_dt, to_dt):
        return self.__getArchiveByDate(MONTH_ARCHIVE, parameters, from_dt, to_dt )

#     @staticmethod
#     def __bytes_to_int(data):
#         return int.from_bytes(data, 'big')

    @staticmethod
    def __bytes_to_float(data):
        return struct.unpack('>f', data[2:4] + data[0:2])[0]

    @staticmethod
    def __bytes_to_double(data):
        return struct.unpack('>d', data[6:8] + data[4:6] + data[2:4] + data[0:2])[0]
