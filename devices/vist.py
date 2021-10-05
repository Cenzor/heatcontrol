from django.utils import timezone
from datetime import datetime as dt
from heatcontrol.devices.modbus.vist import VISTModbus
import time
import socket


def calculate_mean(values: list):
    count = 0
    result = 0
    for val in values:
        if val:
            result += val
            count += 1
    if count > 0:
        return result / count
    else:
        return 0


class Vist:

    def __init__(self, host, port, device_id):
        self.host = host
        self.port = port
        self.hc = None
        self.device_id = int(device_id)

    def connect(self):
        print("connecting to ", (self.host, self.port))
        self.hc = VISTModbus(self.host, self.port, self.device_id, 1)

    def init_session(self):
        connection_attempts = 10
        for i in range(0, connection_attempts):
            try:
                self.connect()
                self.hc.start_session()
                return ""
            except ConnectionRefusedError as ex:
                print('Connection refused. Reconnection...')
                self.close_connection()
                time.sleep(10)
        raise Exception("could not connect to device")
    

    def get_current_time(self):
        date = self.hc.get_device_datetime()
        date = timezone.make_aware(date, timezone.get_current_timezone())
        return date

    def get_archive_records_data(self, file_number, index_start, index_end):
        records = []
        params = ["th", "v1", "v2", "v3", "m1", "m2", "m3", "t1", "t2", "t3", "t4", "p1", "p2", "p3", "q"]

        for i in range(index_start, index_end):
            success = False
            while not success:
                try:
                    record = self.hc.read_archive_file(file_number=file_number, record_number=i)
                    records.append(record)
                    success = True
                except socket.timeout as ex:
                    print('Socket timeout.')
        result = {}
        for p in params:
            if p in ('t1', 't2', 't3', 't4', 'p1', 'p2', 'p3'):
                result[p] = calculate_mean([rec.get(p) for rec in records])
            else:
                result[p] = 0
                for record in records:
                    if p in record.keys():
                        result[p] += record[p]
        return result

    def get_archive(self, archive_type='DAILY'):
        archive_header = self.hc.read_archive_header(file_number=0)
        last_index = archive_header.get('index')
        time_update = dt.strptime(archive_header.get('dt'), '%Y-%m-%d %H:%M:%S')

        if archive_type == 'HOURLY':
            count_records = 1
        elif archive_type == 'DAILY':
            count_records = 24
        elif archive_type == 'MONTHLY':
            date_month_ago = time_update.replace(month=time_update.month - 1)
            count_records = (time_update - date_month_ago).days * 24
        else:
            count_records = last_index - 1

        records = self.get_archive_records_data(
            file_number=0,
            index_start=last_index - count_records,
            index_end=last_index
        )
        return records

    def request_data(self, report_type="DAILY", input_number=1, input_names=[]):
        self.hc.tsys_cnt = input_number
        parameters = [
            't1',
            't2',
            't3',
            't4',
            'p1',
            'p2',
            'p3',
            'v1',
            'v2',
            'v3',
            'm1',
            'm2',
            'm3',
            'w',
            'hv1',
            'hv2',
            'hv3',
            'hm1',
            'hm2',
            'hm3',
            'hq',
            'htw',
        ]
        result = []
        if report_type == "CURRENT":
            try:
                response = self.hc.get_current_values()
            except socket.timeout as ex:
                print('Socket timeout')
                response = self.hc.get_current_values()
            all_data = response['TS' + str(input_number)]
        else:
            response = self.get_archive(report_type)
            all_data = response

        for input_name in input_names:
            if input_name.lower() in all_data.keys():
                result.append(all_data[input_name])
            else:
                result.append(None)
        return (bytearray(), result, "", all_data)

    def close_connection(self):
        self.hc.end_session()        