from heatcontrol.devices.heat_calculators.heat_calculator import HeatCalculator,\
    UnknownParametrName
import datetime
import socket
import struct

HOUR_ARCHIVE = 0x00
DAY_ARCHIVE = 0x01
MONTH_ARCHIVE = 0x02

class TV7HeatCalculator(HeatCalculator):

    __ip = ''
    __port = 0
    __net_address = 0x0



    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port
        self. __net_address = 0x00

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
        request_number = 0x0
        message = [self.__net_address, 0x48, 0x1E, 0x88, 0x00, 0x03, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, request_number]
        message = bytes(message)
        message += self.__crc16(message)
        sock.send(message)
        recv = sock.recv(1024)
        return datetime.datetime(year=2000+recv[9], month=recv[6], day=recv[7],
            hour=recv[8], minute=recv[11], second=recv[10])
        sock.close()

    def getCurrentValues(self, parameters):
        s = socket.socket()
        s.connect((self.__ip, self.__port))
        s.settimeout(20)
        request_number = 0x0
        m = [self.__net_address, 0x48, 0x1E, 0x88, 0x00, 0x89, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, request_number]
        m = bytes(m)
        m += self.__crc16(m)
        s.send(m)
        r = s.recv(1024)
        request_number = 0x1
        m = [self.__net_address, 0x48, 0x1D, 0x88, 0x00, 0x89, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, request_number]
        m = bytes(m)
        m += self.__crc16(m)
        s.send(m)
        r += s.recv(1024)
        offsets = {
            'ТВ1.t1': (12, 16, self.__bytes_to_float),
            'ТВ1.t2': (16, 20, self.__bytes_to_float),
            'ТВ1.t3': (20, 24, self.__bytes_to_float),
            'ТВ2.t1': (24, 28, self.__bytes_to_float),
            'ТВ2.t2': (28, 32, self.__bytes_to_float),
            'ТВ2.t3': (32, 36, self.__bytes_to_float),
            #36-40
            'ТВ1.P1': (40, 44, self.__bytes_to_float),
            'ТВ1.P2': (44, 48, self.__bytes_to_float),
            'ТВ1.P3': (48, 52, self.__bytes_to_float),
            'ТВ2.P1': (52, 56, self.__bytes_to_float),
            'ТВ2.P2': (56, 60, self.__bytes_to_float),
            'ТВ2.P3': (60, 64, self.__bytes_to_float),
            #64-68
            'ТВ1.Gо1': (68, 72, self.__bytes_to_float),#Кирилица!
            'ТВ1.Gо2': (72, 76, self.__bytes_to_float),
            'ТВ1.Gо3': (76, 80, self.__bytes_to_float),
            'ТВ2.Gо1': (80, 84, self.__bytes_to_float),
            'ТВ2.Gо2': (84, 88, self.__bytes_to_float),
            'ТВ2.Gо3': (88, 92, self.__bytes_to_float),
            #92-96
            'ТВ1.Gм1': (96, 100, self.__bytes_to_float),
            'ТВ1.Gм2': (100, 104, self.__bytes_to_float),
            'ТВ1.Gм3': (104, 108, self.__bytes_to_float),
            'ТВ2.Gм1': (108, 112, self.__bytes_to_float),
            'ТВ2.Gм2': (112, 116, self.__bytes_to_float),
            'ТВ2.Gм3': (116, 120, self.__bytes_to_float),
            #120-124
            'ТВ1.Ф1': (124, 128, self.__bytes_to_float),
            'ТВ1.Ф2': (128, 132, self.__bytes_to_float),
            'ТВ1.Ф3': (132, 136, self.__bytes_to_float),
            'ТВ2.Ф1': (136, 140, self.__bytes_to_float),
            'ТВ2.Ф2': (140, 144, self.__bytes_to_float),
            'ТВ2.Ф3': (144, 148, self.__bytes_to_float),
            #Итоговый архив
            'ТВ1.V1': (294, 302, self.__bytes_to_double),
            'ТВ1.M1': (302, 310, self.__bytes_to_double),
            'ТВ1.V2': (310, 318, self.__bytes_to_double),
            'ТВ1.M2': (318, 326, self.__bytes_to_double),
            'ТВ1.V3': (326, 334, self.__bytes_to_double),
            'ТВ1.M3': (334, 342, self.__bytes_to_double),
            'ТВ2.V1': (342, 350, self.__bytes_to_double),
            'ТВ2.M1': (350, 358, self.__bytes_to_double),
            'ТВ2.V2': (358, 366, self.__bytes_to_double),
            'ТВ2.M2': (366, 374, self.__bytes_to_double),
            'ТВ2.V3': (374, 382, self.__bytes_to_double),
            'ТВ2.M3': (382, 390, self.__bytes_to_double),
            #390-406
            'ТВ1.dM': (406, 414, self.__bytes_to_double),
            'ТВ1.Qтв': (414, 422, self.__bytes_to_double),
            'ТВ1.Q12': (422, 430, self.__bytes_to_double),
            'ТВ1.Qг': (430, 438, self.__bytes_to_double),
            'ТВ1.ВНР': (438, 440, self.__bytes_to_int),
            'ТВ1.ВОС': (440, 442, self.__bytes_to_int),
            'ТВ1.TVmin': (442, 444, self.__bytes_to_int),
            'ТВ1.TVmax': (444, 446, self.__bytes_to_int),
            'ТВ1.Tdt': (446, 448, self.__bytes_to_int),
            'ТВ1.Tбез.пит.': (448, 450, self.__bytes_to_int),
            'ТВ1.Tнеиспр.': (450, 452, self.__bytes_to_int),
            'ТВ2.dM': (452, 460, self.__bytes_to_double),
            'ТВ2.Qтв': (460, 468, self.__bytes_to_double),
            'ТВ2.Q12': (468, 474, self.__bytes_to_double),
            'ТВ2.Qг': (474, 482, self.__bytes_to_double),
            'ТВ2.ВНР': (482, 484, self.__bytes_to_int),
            'ТВ2.ВОС': (484, 486, self.__bytes_to_int),
            'ТВ2.TVmin': (486, 488, self.__bytes_to_int),
            'ТВ2.TVmax': (488, 490, self.__bytes_to_int),
            'ТВ2.Tdt': (490, 492, self.__bytes_to_int),
            'ТВ2.Tбез.пит.': (492, 494, self.__bytes_to_int),
            'ТВ2.Tнеиспр.': (494, 496, self.__bytes_to_int),
        }
        result = {}
        for parameter in parameters:
            if parameter in offsets:
                o = offsets[parameter]
                result[parameter] = o[2](r[o[0]:o[1]])
            else:
                raise UnknownParametrName('Unknown parameter \'{}\''.format(parameter))
        s.close()
        return result

    def __getArchives(self, archive_type, parameters, from_dt, to_dt):
        report_date = from_dt
        result = []
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
            s = socket.socket()
            s.connect((self.__ip, self.__port))
            s.settimeout(20)
            request_number = 0x0
            message = [self.__net_address, 0x48, 0x00, 0x00, 0x00, 0x00, 0x00, 0x63, 0x00, 0x06,
                0x00, 0x0C,
                0x00, request_number,
                m, d,
                h, y,
                0x00, 0x00,
                0x00, archive_type,
                0x00, 0x00,
                0x00,0x00,
            ]
            message = bytes(message)
            message += self.__crc16(message)
            s.send(message)
            r = s.recv(1024)


            request_number += 1
            message = [self.__net_address, 0x48, 0x1B, 0x88, 0x00, 0x8E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, request_number ]
            message = bytes(message)
            message += self.__crc16(message)
            s.send(message)
            r = s.recv(1024)
            if 0xC8 == r[1]:
                print('Archive didn\'t have records at this date')
                continue
            elif 0x48 != r[1]:
                print('Error')
                continue
            result_record = {'datetime': datetime.datetime(year=r[9]+2000, month=r[6], day=r[7], hour=r[8])}
            offsets = {
                'ТВ1.t1': (10, 14, self.__bytes_to_float),
                'ТВ1.P1': (14, 18, self.__bytes_to_float),
                'ТВ1.V1': (18, 22, self.__bytes_to_float),
                'ТВ1.M1': (22, 26, self.__bytes_to_float),
                'ТВ1.t2': (26, 30, self.__bytes_to_float),
                'ТВ1.P2': (30, 34, self.__bytes_to_float),
                'ТВ1.V2': (34, 38, self.__bytes_to_float),
                'ТВ1.M2': (38, 42, self.__bytes_to_float),
                'ТВ1.t3': (42, 46, self.__bytes_to_float),
                'ТВ1.P3': (46, 50, self.__bytes_to_float),
                'ТВ1.V3': (50, 54, self.__bytes_to_float),
                'ТВ1.M3': (54, 58, self.__bytes_to_float),
                'ТВ2.t1': (58, 62, self.__bytes_to_float),
                'ТВ2.P1': (62, 66, self.__bytes_to_float),
                'ТВ2.V1': (66, 70, self.__bytes_to_float),
                'ТВ2.M1': (70, 74, self.__bytes_to_float),
                'ТВ2.t2': (74, 78, self.__bytes_to_float),
                'ТВ2.P2': (78, 82, self.__bytes_to_float),
                'ТВ2.V2': (82, 86, self.__bytes_to_float),
                'ТВ2.M2': (86, 90, self.__bytes_to_float),
                'ТВ2.t3': (90, 94, self.__bytes_to_float),
                'ТВ2.P3': (94, 98, self.__bytes_to_float),
                'ТВ2.V3': (98, 102, self.__bytes_to_float),
                'ТВ2.M3': (102, 106, self.__bytes_to_float),
                #108-126
                'ТВ1.tнв': (122, 126, self.__bytes_to_float),
                'ТВ1.tx': (126, 130, self.__bytes_to_float),
                'ТВ1.Px': (130, 134, self.__bytes_to_float),
                'ТВ1.dt': (134, 138, self.__bytes_to_float),
                'ТВ1.dM': (138, 142, self.__bytes_to_float),
                'ТВ1.Qтв': (142, 146, self.__bytes_to_float),
                'ТВ1.Q12': (146, 150, self.__bytes_to_float),
                'ТВ1.Qг': (150, 154, self.__bytes_to_float),
                'ТВ1.ВНР': (154, 156, self.__bytes_to_int),
                'ТВ1.ВОС': (156, 158, self.__bytes_to_int),
                'ТВ2.tнв': (158, 162, self.__bytes_to_float),
                'ТВ2.tx': (162, 166, self.__bytes_to_float),
                'ТВ2.Px': (166, 170, self.__bytes_to_float),
                'ТВ2.dt': (170, 174, self.__bytes_to_float),
                'ТВ2.dM': (174, 178, self.__bytes_to_float),
                'ТВ2.Qтв': (178, 182, self.__bytes_to_float),
                'ТВ2.Q12': (182, 186, self.__bytes_to_float),
                'ТВ2.Qг': (186, 190, self.__bytes_to_float),
                'ТВ2.ВНР': (190, 192, self.__bytes_to_int),
                'ТВ2.ВОС': (192, 194, self.__bytes_to_int),

            }

            for parameter in parameters:
                if parameter in offsets:
                    o = offsets[parameter]
                    result_record[parameter] = o[2](r[o[0]:o[1]])
                else:
                    raise UnknownParametrName('Unknown parameter \'{}\''.format(parameter))
            s.close()
            result.append(result_record)
        return result

    def getHourArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(HOUR_ARCHIVE, parameters, from_dt, to_dt )

    def getDayArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(DAY_ARCHIVE, parameters, from_dt, to_dt )


    def getMonthArchives(self, parameters, from_dt, to_dt):
        return self.__getArchives(MONTH_ARCHIVE, parameters, from_dt, to_dt )
