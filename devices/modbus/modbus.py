# -*- coding:utf-8 -*-
import socket
from datetime import datetime


class TCPModbusClient:

    def __init__(self, host: str, port: int, device_id: int):
        self.host = host
        self.port = port
        self.device_id = device_id.to_bytes(1, "big")
        self.__sock = socket.socket()
        self.__sock.settimeout(10)

    def connect(self):
        self.__sock.connect((self.host, self.port))
        self.__sock.settimeout(20)

    def close(self):
        self.__sock.close()

    def __make_request(self, byte_string: bytes):
        request = byte_string + self.crc16(byte_string)
        self.__sock.send(request)
        response = self.__sock.recv(512)
        if response[-2:] != self.crc16(response[:-2]) or response[1] & (1 << 7) != 0:
            raise Exception(f'Error {request.hex()}, {response.hex()}')
        return response

    def read_holding_registers(self, offset: bytes, registers_count: bytes):
        response = self.__make_request(self.device_id + b'\x03' + offset + registers_count)
        return response[3:-2]

    def read_input_registers(self, offset: bytes, registers_count: bytes):
        response = self.__make_request(self.device_id + b'\x04' + offset + registers_count)
        return response[3:-2]

    def read_file_record(self, byte_count: bytes, file_number: bytes,
                         record_number: bytes, length: bytes):
        response = self.__make_request(self.device_id + b'\x14' + byte_count + b'\x06'
                                       + file_number + record_number + length)
        return response[5:-2]

    @staticmethod
    def crc16(byte_string: bytes):
        crc = 0xFFFF
        length = len(byte_string)
        for x in range(0, length):
            crc = int(crc / 256) * 256 + crc % 256 ^ byte_string[x]
            for y in range(0, 8):
                if crc & 0x1:
                    crc = (crc >> 1) ^ 0xa001
                else:
                    crc >>= 1
        return crc.to_bytes(2, "little")

    @staticmethod
    def datetime_from_bytes(byte_string: bytes):
        return datetime(2000 + byte_string[5], byte_string[4],
                        byte_string[3], byte_string[0],
                        byte_string[1], byte_string[2])

    @staticmethod
    def parse_bytes(byte_string: bytes, size: int, sep: int):
        response = list()
        x, y = 0, sep
        for i in range(int(size / sep)):
            num = int.from_bytes(byte_string[x:y], "big")
            response.append(num)
            x, y = y, y + sep
        return response
