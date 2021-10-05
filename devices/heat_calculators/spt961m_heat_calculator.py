from . import *
import datetime
import socket
import re
from heatcontrol.devices.heat_calculators.heat_calculator import HeatCalculator


HOUR_ARCHIVE = 65530
DAY_ARCHIVE = 65532
MONTH_ARCHIVE = 65534

DLE = b'\x10'
SOH = DLE + b'\x01'
ISI = DLE + b'\x1f'
STX = DLE + b'\x02'
ETX = DLE + b'\x03'
HT  = b'\x09'
FF  = b'\x0c'

class SPT961MHeatCalculator(HeatCalculator):

    __ip = ''
    __port = 0

    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port

    @staticmethod
    def __crc16(data):
        crc = 0x0
        l = len(data)
        i = 0
        for x in range(0, l):
            crc = crc ^ data[x] << 8
            for y in range(0, 8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            crc &= 0xFFFF
        return (crc & 0xFFFF).to_bytes(2, 'big')


    def getSettings(self, parameters):
        pass

    def getCurrentTime(self):
        s = socket.socket()
        s.connect((self.__ip, self.__port))
        s.settimeout(20)

        # needs get 2 parameters: 060 - date and 061 - current time
        message = ISI + b'\x1d' + STX + HT + '0'.encode('cp866') + HT + '060'.encode('cp866') + FF + HT + '0'.encode('cp866')+ HT +'061'.encode('cp866') + FF + ETX
        message = SOH + message + self.__crc16(message)

        s.send(message)

        params = s.recv(1024)

        params = params[7:-4]
        #Split message by FF
        params = params.split(b'\x0c')[1:]
        md = re.match('^\t(\d{2})-(\d{2})-(\d{2})\tдд-мм-гг$'.encode('cp866'), params[0])
        mt = re.match('^\t(\d{2}):(\d{2}):(\d{2})\tчч:мм:сс$'.encode('cp866'), params[2])
        s.close()
        return datetime.datetime(year=int(md.group(3))+2000, month=int(md.group(2)), day=int(md.group(1)), hour=int(mt.group(1)), minute=int(mt.group(2)), second=int(mt.group(3)))

    def getCurrentValues(self, parameters):
        raise

    def __getArchives(self, archive_type, parameters, from_dt, to_dt):
        report_date = from_dt
        result = []

        s = socket.socket()
        s.connect((self.__ip, self.__port))
        s.settimeout(20)

        message = ISI + b'\x19' + STX + HT + '0'.encode('cp1251') + HT + '{}'.format(archive_type).encode('cp1251') + FF +  ETX
        message = SOH + message + self.__crc16(message)

        s.send(message)
        params = s.recv(1024)
        # Cut SOH, ISI, FHC, STX ahead, and  ETX, CRC behind
        params = params[7:-4]
        #Split message by FF
        params = params.split(b'\x0c')[1:]

        while(report_date <= to_dt):
            d = report_date.day
            m = report_date.month
            y = report_date.year
            h = report_date.hour
            if HOUR_ARCHIVE == archive_type:
                report_date += datetime.timedelta(hours=1)
            if DAY_ARCHIVE == archive_type:
                report_date += datetime.timedelta(days=1)
            if MONTH_ARCHIVE == archive_type:
                report_date = (report_date.replace(day=1) + datetime.timedelta(days=31)).replace(day=1)

            message = ISI + b'\x18' + STX + HT + '0'.encode('cp866') + HT + '65532'.encode('cp866') + FF + \
            HT + '{}'.format(d).encode('cp866') + HT + '{}'.format(m).encode('cp866') + HT + '{}'.format(y).encode('cp866') + HT + '{}'.format(h).encode('cp866') + HT + '00'.encode('cp866') + HT + '00'.encode('cp866') + FF + ETX
            message = SOH + message + self.__crc16(message)

            s.send(message)
            values = s.recv(1024)
            values = values[7:-4]

            values = values.split(b'\x0c')

            if '\tНет данных?'.encode('cp866') == values[4]:
                continue
            parse_date = values[2].split('\t'.encode('cp866'))[1:]
            result_record = {'datetime': datetime.datetime(year=int(parse_date[2])+2000, month=int(parse_date[1]), day=int(parse_date[0]), hour=int(parse_date[3]))}
            for parameter in parameters:
                result_record[parameter] = None
            values = values[4:]
            for i in range(len(values)-1):
                local_params = params[i].split(b'\t')[1:]
                local_values = values[i].split(b'\t')[1:]
                if local_params[0].decode('cp866') in result_record.keys():
                    result_record[local_params[0].decode('cp866')] = local_values[0].decode('cp866')
            result.append(result_record)
        s.close()
        return result

    def getHourArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(HOUR_ARCHIVE, parameters, from_dt, to_dt )

    def getDayArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(DAY_ARCHIVE, parameters, from_dt, to_dt )


    def getMonthArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(MONTH_ARCHIVE, parameters, from_dt, to_dt )
