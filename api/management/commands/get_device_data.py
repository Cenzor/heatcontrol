from django.core.management.base import BaseCommand, CommandError
from heatcontrol.api.models import MeteringPoint, MeteringPointData
from django.utils import timezone
from heatcontrol.devices.utils import get_device_obj

class Command(BaseCommand):
    help = 'get data from device'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('metering_point_id', nargs='+', type=int)
        parser.add_argument('report_type', nargs='+', type=str)

    def handle(self, *args, **options):
        metering_point_id = options["metering_point_id"]
        metering_point_id = metering_point_id[0]
        report_type = options["report_type"]
        report_type = report_type[0]
        metering_point = MeteringPoint.objects.get(id = metering_point_id)
        modem = metering_point.modem
        device = metering_point.device
        #TODO use device type data
        log = ""
        connection_string = device.connection_string
        if not connection_string:
            connection_string = modem.connection_string
        log += '\nconnection_string: ' + connection_string
        connection_values = connection_string.split(":")
        device_type = metering_point.device.device_type
        device_obj = get_device_obj(device_type.model, connection_values[0], connection_values[1], device)
        log += "\nconnecting to device... "
        log += "\n" + device_obj.init_session()
#         log += "\ngetting service info..."
#         data = bkt7.get_service_info()
#         log += '\nномер версии ПО: {}'.format(bkt7.software_version(data[3]))
#         log += '\nсхема измерения ТВ1: {}'.format(data[4:6].hex())
#         log += '\nсхема измерения ТВ2: {}'.format(data[6:8].hex())
#         log += '\nидентификатор абонента: {}'.format(data[8:16].hex())
#         log += '\nсетевой номер прибора: {}'.format(data[16:17].hex())
#         log += '\nдата отчета: {}'.format(data[17:18].hex())
#         log += '\nмодель исполнения: {}'.format(data[18:19].hex())
        date = device_obj.get_current_time()
        log += "\ndevice time = %s " % date
        log += "\nrequesting data... "
        try:
            input_number = int(metering_point.input_number)
        except Exception as ex:
            input_number = 1
        raw_data, data, request_log, all_data = device_obj.request_data(report_type, input_number, metering_point.device.device_type.parameters)
        device_obj.close_connection()
        log += request_log
#         print("got data:", data)
        print(log)
        print("data = ", data)
        metering_point_data = MeteringPointData(
            metering_point = metering_point,
            device_type = device.device_type,
            timestamp = date,
            #FIXME replace data
            data = data,
            raw_data = raw_data,
            log = log,
            all_data = all_data,
            report_type=report_type,
        )
        metering_point_data.save()
        metering_point_data.calculate_data()
        device.set_status("ONLINE")
#         print(log)
        print("done.")