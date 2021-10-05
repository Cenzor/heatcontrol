# -*- coding:utf-8 -*-
from .modbus import TCPModbusClient
import json


class VISTModbus(TCPModbusClient):

    TSYS_CURRENT = (
        ((b'\x02\x00', b'\x00\x25'),
         (b'\x03\x06', b'\x00\x1c'),
         (b'\x04\x00', b'\x00\x37')),

        ((b'\x06\x00', b'\x00\x25'),
         (b'\x07\x06', b'\x00\x1c'),
         (b'\x08\x00', b'\x00\x37')),

        ((b'\x0a\x00', b'\x00\x25'),
         (b'\x0b\x06', b'\x00\x1c'),
         (b'\x0c\x00', b'\x00\x37')),
    )

    ARCH_PARAMS = (
        ('th', 1), ('v1', 4), ('v2', 4),
        ('v3', 4), ('m1', 4), ('m2', 4),
        ('m3', 4), ('t1', 2), ('t2', 2),
        ('t3', 2), ('t4', 2), ('p1', 1),
        ('p2', 1), ('p3', 1), ('q', 4),
    )

    def __init__(self, host: str, port: int, device_id: int, tsys_count: int):
        super().__init__(host, port, device_id)
        self.tsys_cnt = tsys_count
        self.current_values = dict()
        self.archive_header = dict()
        self.device_settings = dict()

    def start_session(self):
        self.connect()

    def end_session(self):
        self.close()

    def __enter__(self):
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_session()

    def get_device_settings(self):
        response = self.read_holding_registers(b'\x00\x00', b'\x00\x63')
        self.device_settings.update({
            'soft_version': response[4:25].decode('cp1251').replace('\x00', ''),
            'device_type': response[25:46].decode('cp1251').replace('\x00', ''),
            'serial_number': response[46:81].decode('cp1251').replace('\x00', ''),
            'interface': int.from_bytes(response[89:91], "big"),
            'speed': int.from_bytes(response[91:93], "big"),
            'modem': int.from_bytes(response[93:95], "big"),
            'device_id': int.from_bytes(response[95:97], "big")
        })
        return self.device_settings

    def get_device_datetime(self):
        response = self.read_input_registers(b'\x00\x00', b'\x00\x03')
        return self.datetime_from_bytes(response)

    def get_current_values(self):
        self.current_values['dt'] = str(self.get_device_datetime())
        for t in range(self.tsys_cnt):
            response = [
                self.read_input_registers(self.TSYS_CURRENT[t][r][0], self.TSYS_CURRENT[t][r][1])
                for r in range(len(self.TSYS_CURRENT[t]))]
            precision_bytes = response[0][4:12] + response[2][4:12]
            precision = [10**p for p in self.parse_bytes(precision_bytes, 16, 2)]
            self.current_values['TS' + str(t + 1)] = {
                't1': int.from_bytes(response[0][12:14], "big") / 100,
                't2': int.from_bytes(response[0][14:16], "big") / 100,
                't3': int.from_bytes(response[0][16:18], "big") / 100,
                't4': int.from_bytes(response[0][18:20], "big") / 100,
                'p1': int.from_bytes(response[0][68:70], "big") / 10,
                'p2': int.from_bytes(response[0][70:72], "big") / 10,
                'p3': int.from_bytes(response[0][72:74], "big") / 10,
                'v1': int.from_bytes(response[1][0:4], "big") / precision[0],
                'v2': int.from_bytes(response[1][4:8], "big") / precision[1],
                'v3': int.from_bytes(response[1][8:12], "big") / precision[2],
                'm1': int.from_bytes(response[1][24:28], "big") / precision[0],
                'm2': int.from_bytes(response[1][28:32], "big") / precision[1],
                'm3': int.from_bytes(response[1][32:36], "big") / precision[2],
                'w': int.from_bytes(response[1][52:60], "big") / precision[3],
                'hv1': int.from_bytes(response[2][36:40], "big") / (precision[4] * 3600),
                'hv2': int.from_bytes(response[2][40:44], "big") / (precision[5] * 3600),
                'hv3': int.from_bytes(response[2][44:48], "big") / (precision[6] * 3600),
                'hm1': int.from_bytes(response[2][48:52], "big") / (precision[4] * 3600),
                'hm2': int.from_bytes(response[2][52:56], "big") / (precision[5] * 3600),
                'hm3': int.from_bytes(response[2][56:60], "big") / (precision[6] * 3600),
                'hq': int.from_bytes(response[2][104:108], "big") / (precision[7] * 1200),
                'htw': int.from_bytes(response[2][108:110], "big") / (100 * 36),
            }
        return self.current_values

    def read_archive_header(self, file_number: int):
        response = self.read_file_record(b'\xf5', file_number.to_bytes(2, "big"), b'\x00\x00', b'\x00\x30')
        archive_header = {
            'count': int.from_bytes(response[10:12], "big"),
            'index': int.from_bytes(response[12:14], "big"),
            'max_count': int.from_bytes(response[14:16], "big"),
            'dt': str(self.datetime_from_bytes(response[16:22])),
            'Tt': int.from_bytes(response[46:50], "big"),
            'Qt': int.from_bytes(response[50:58], "big"),
            'precision': self.parse_bytes(response[58:62], 4, 1),
            'param_mask': int.from_bytes(response[6:10], "big"),
        }
        for i, n in enumerate(self.parse_bytes(response[22:34], 12, 4)):
            archive_header['Vt' + str(i + 1)] = n / (10 ** archive_header['precision'][i])
        for i, n in enumerate(self.parse_bytes(response[34:46], 12, 4)):
            archive_header['Mt' + str(i + 1)] = n / (10 ** archive_header['precision'][i])
        archive_header['Qt'] /= 10 ** archive_header['precision'][-1]
        archive_header['Tt'] /= 100
        self.archive_header[file_number] = archive_header
        return self.archive_header[file_number]

    def read_archive_file(self, file_number: int, record_number: int):
        if not self.archive_header[file_number]:
            self.read_archive_header(file_number)
        base, archive_file = 1, {'id': record_number}
        arch_precision, param_mask = (self.archive_header[file_number]['precision'],
                                      self.archive_header[file_number]['param_mask'])
        precision = [2] + arch_precision[:3] * 2 + [1] * 7 + [arch_precision[-1]]
        response = self.read_file_record(b'\xf5', file_number.to_bytes(2, "big"),
                                         record_number.to_bytes(2, "big"), b'\x00\x30')
        for i, param in enumerate(self.ARCH_PARAMS):
            if param_mask & 1 << i:
                offset = base + param[1]
                archive_file[param[0]] = int.from_bytes(response[base: offset], "big") / 10**precision[i]
                base = offset
        return archive_file

    def to_json(self):
        serialize = {
            'device_settings': self.device_settings,
            'current_values': self.current_values,
            'archive_header': self.archive_header
        }
        return json.dumps(serialize)
