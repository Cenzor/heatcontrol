from django.db import models
from django.contrib.auth.models import AbstractUser
from model_utils.models import TimeStampedModel
from django.utils import timezone


class Company(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=512, blank=True, null=True)
    address_coords = models.JSONField(blank=True, null=True)
    company_type = models.CharField(max_length=255, blank=True, null=True)
    fias_code = models.CharField(max_length=255, blank=True, null=True)
    inn = models.CharField(max_length=64, blank=True, null=True)
    phone = models.CharField(max_length=64, blank=True, null=True)
    fax = models.CharField(max_length=64, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    parent_company_id = models.PositiveIntegerField(blank = True, null = True)
    created_date = models.DateTimeField(blank=True, null=True)
    tariff = models.CharField(max_length=255, blank=True, null=True)
    departments = models.JSONField(blank = True, null = True)
    tags = models.JSONField(blank = True, null = True)
    logo = models.ImageField(upload_to='company/%Y/%m/%d', blank=True, null=True)
    timezone = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default = False, db_index = True)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for user in User.objects.filter(employer = self):
            user.delete()
        for company_object in CompanyObject.objects.filter(company = self):
            company_object.delete()
        for department in Department.objects.filter(company = self):
            department.delete()
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    patronymic = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=64, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True) #deprecated
    department = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=256, blank=True, null=True)
    position = models.CharField(max_length=256, blank=True, null=True)
    employer = models.ForeignKey(Company, on_delete = models.CASCADE, blank = True, null = True)
    avatar = models.ImageField(upload_to='user/%Y/%m/%d', blank=True, null=True)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def get_permissions(self):
        role = self.role
        if not role:
            role = "default"
        permissions = UserPermissions.objects.filter(role = role)[:1]
        if permissions.count():
            return permissions[0]
        return None
            

class UserPermissions(models.Model):
    role = models.CharField(max_length=256)
    status_admin_system = models.BooleanField(default = False)
    status_admin_company = models.BooleanField(default = False)
    status_admin_company_object = models.BooleanField(default = False)
    status_admin_modem = models.BooleanField(default = False)
    status_admin_device = models.BooleanField(default = False)

    def __str__(self):
        return self.role


class CompanyObject(TimeStampedModel):
    MOVE_RESOURCE = [
        (u'RSO', u'РСО'),
        (u'TSO', u'ТСО'),
        (u'UK', u'УК'),
        (u'USER', u'Потребитель')
    ]
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete = models.CASCADE, blank = True, null = True)
    address = models.CharField(max_length=512, blank=True, null=True)
    address_coords = models.JSONField(blank=True, null=True)
    object_type = models.CharField(max_length=255, blank=True, null=True)
    move_resource = models.CharField(max_length=15, choices=MOVE_RESOURCE, blank=True,
                                     null=True, verbose_name='Движение ресурса', default='RSO')
    mode = models.CharField(max_length=255, blank=True, null=True)
    mode_switch_date = models.DateTimeField(blank=True, null=True)
    timezone = models.CharField(max_length=255, blank=True, null=True)
    fias = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    tags = models.JSONField(blank = True, null = True)
    deleted = models.BooleanField(default = False, db_index = True)
    t1_min = models.FloatField(blank=True, null=True)
    t1_max = models.FloatField(blank=True, null=True)
    t2_min = models.FloatField(blank=True, null=True)
    t2_max = models.FloatField(blank=True, null=True)
    dt_min = models.FloatField(blank=True, null=True)
    dt_max = models.FloatField(blank=True, null=True)
    p1_min = models.FloatField(blank=True, null=True)
    p1_max = models.FloatField(blank=True, null=True)
    p2_min = models.FloatField(blank=True, null=True)
    p2_max = models.FloatField(blank=True, null=True)
    dp_min = models.FloatField(blank=True, null=True)
    dp_max = models.FloatField(blank=True, null=True)
    q1_min = models.FloatField(blank=True, null=True)
    q1_max = models.FloatField(blank=True, null=True)
    q2_min = models.FloatField(blank=True, null=True)
    q2_max = models.FloatField(blank=True, null=True)
    dq_min = models.FloatField(blank=True, null=True)
    dq_max = models.FloatField(blank=True, null=True)
    heating_season_start_date = models.DateTimeField(blank=True, null=True)
    heating_season_enabled_date = models.DateTimeField(blank=True, null=True)
    object_category = models.JSONField(blank = True, null = True)
    

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for modem in Modem.objects.filter(company_object = self):
            modem.delete()
        for device in Device.objects.filter(company_object = self):
            device.delete()
        for metering_point in MeteringPoint.objects.filter(company_object = self):
            metering_point.delete()

    def __str__(self):
        return self.name


class CompanyObjectWeatherData(TimeStampedModel):
    company_object = models.ForeignKey(CompanyObject, on_delete = models.CASCADE, blank = True, null = True)
    data = models.JSONField(blank=True, null=True)

    
class Modem(TimeStampedModel):
    model = models.CharField(max_length=255)
    company_object = models.ForeignKey(CompanyObject, on_delete = models.CASCADE, blank = True, null = True)
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    auto_off = models.BooleanField(default = False)
    apn = models.CharField(max_length=255, blank=True, null=True)
    speed_code1 = models.FloatField(blank=True, null=True)
    speed_code2 = models.FloatField(blank=True, null=True)
    speed_code3 = models.FloatField(blank=True, null=True)
    allow_connection = models.BooleanField(default = False)
    connection_string = models.CharField(max_length=255, blank=True, null=True)
    edge_enabled = models.BooleanField(default = False)
    firmware_version = models.CharField(max_length=255, blank=True, null=True)
    gps_class = models.CharField(max_length=255, blank=True, null=True)
    gprs_setings_setup = models.CharField(max_length=255, blank=True, null=True)
    sim_identifier = models.CharField(max_length=255, blank=True, null=True)
    device_identifier = models.CharField(max_length=255, blank=True, null=True)
    interface_code1 = models.CharField(max_length=255, blank=True, null=True)
    interface_code2 = models.CharField(max_length=255, blank=True, null=True)
    interface_code3 = models.CharField(max_length=255, blank=True, null=True)
    login = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=255, blank=True, null=True)
    signal_level = models.FloatField(blank=True, null=True)
    sms_center = models.CharField(max_length=255, blank=True, null=True)
    mac_address = models.CharField(max_length=255, blank=True, null=True)
    imei = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default = True)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for device in Device.objects.filter(modem = self):
            device.delete()
        for metering_point in MeteringPoint.objects.filter(modem = self):
            metering_point.delete()

    def __str__(self):
        return self.model
    
    
DEVICE_MODELS = (
    (u'ВКТ-7', u'ВКТ-7'),
    (u'ТВ-7', u'ТВ-7'),
    (u'spt961m', u'spt961m'),
    (u'carat307', u'carat307'),
    (u'elf04', u'elf04'),
    (u'TSRV043', u'TSRV043'),
    (u'vist', u'vist'),
    (u'sa94', u'sa94'),
)
class DeviceType(TimeStampedModel):
    name = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=50, choices=DEVICE_MODELS, default='ВКТ-7', db_index=True)
    parameters = models.JSONField(blank=True, null=True, help_text = "Список параметров для отчета")
    parameter_units = models.JSONField(blank=True, null=True, help_text = "Список единиц измерения для отчета")
    current_report_parameters = models.JSONField(blank=True, null=True, help_text = "Список параметров для текущего отчета")
    current_report_parameter_units = models.JSONField(blank=True, null=True, help_text = "Список единиц измерения для текущего отчета")
    deleted = models.BooleanField(default = False, db_index = True)
    template_pdf = models.CharField(max_length=512, blank=True, null=True, help_text = "Путь к шаблону отчета")
    template_xls = models.CharField(max_length=512, blank=True, null=True, help_text = "Путь к шаблону отчета")
    template_docx = models.CharField(max_length=512, blank=True, null=True, help_text = "Путь к шаблону отчета")
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for metering_point_data in MeteringPointData.objects.filter(device_type = self):
            metering_point_data.delete()

    def __str__(self):
        return self.name
    
    def get_template_file_name(self, file_type):
        if file_type == "PDF":
            if self.template_pdf:
                return self.template_pdf
            return "report_many_pages.html"
        if file_type == "DOCX":
            if self.template_docx:
                return self.template_docx
            return "report.docx"
        raise Exception("unknown file type: %s" % file_type)


class ModemType(TimeStampedModel):
    name = models.CharField(max_length=255)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.name


class SensorType(TimeStampedModel):
    name = models.CharField(max_length=255)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.name
    
    
class FlowMeterType(TimeStampedModel):
    name = models.CharField(max_length=255)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.name

    
DEVICE_STATUSES = (
    (u'ONLINE', u'ONLINE'),
    (u'OFFLINE', u'OFFLINE'),
    (u'DISABLED', u'DISABLED'),
)        
class Device(TimeStampedModel):
    name = models.CharField(max_length=255, blank = True, null = True)
    status = models.CharField(max_length=50, choices=DEVICE_STATUSES, default='ONLINE', db_index=True)
    status_changed_date = models.DateTimeField(blank = True, null = True)
    company_object = models.ForeignKey(CompanyObject, on_delete = models.CASCADE, blank = True, null = True)
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    network_address = models.CharField(max_length=255, blank=True, null=True)
    modification = models.CharField(max_length=255, blank=True, null=True)
    speed = models.PositiveIntegerField(blank=True, null=True)
    service_company = models.CharField(max_length=255, blank=True, null=True)
    data_format = models.CharField(max_length=255, blank=True, null=True)
    channel = models.CharField(max_length=255, blank=True, null=True)
    driver_version = models.CharField(max_length=255, blank=True, null=True)
    driver_version = models.CharField(max_length=255, blank=True, null=True)
    current_check_date = models.DateTimeField(blank = True, null = True)
    next_check_date = models.DateTimeField(blank = True, null = True)
    sealing_date = models.DateTimeField(blank = True, null = True)
    device_time = models.CharField(max_length=255, blank = True, null = True)
    gis_number = models.CharField(max_length=255, blank=True, null=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    accounting_type = models.CharField(max_length=255, blank=True, null=True)
    owner = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    modem = models.ForeignKey(Modem, on_delete = models.CASCADE, blank = True, null = True)
    parameters = models.JSONField(blank=True, null=True)
    device_type = models.ForeignKey(DeviceType, on_delete = models.CASCADE, blank = True, null = True)
    deleted = models.BooleanField(default = False, db_index = True)
    sensors = models.JSONField(blank = True, null = True)
    flow_meters = models.JSONField(blank = True, null = True)
    connection_string = models.CharField(max_length=255, blank=True, null=True)
    
    def set_status(self, status):
        if not self.status == status:
            self.status = status
            self.status_changed_date = timezone.now()
            self.save(update_fields = ["status", "status_changed_date"])
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for sensor in Sensor.objects.filter(device = self):
            sensor.delete()
        for flow_meter in FlowMeter.objects.filter(device = self):
            flow_meter.delete()

    def __str__(self):
        if self.name:
            return self.name
        if self.device_type:
            return self.device_type.name
        return str(self.id)


class BusyDevice(TimeStampedModel):
    device = models.ForeignKey(Device, on_delete = models.CASCADE, blank = True, null = True)


class Sensor(TimeStampedModel):
    model = models.CharField(max_length=255)
    device = models.ForeignKey(Device, on_delete = models.CASCADE, blank = True, null = True)
    modification = models.CharField(max_length=255, blank=True, null=True)
    value_min = models.CharField(max_length=255, blank=True, null=True)
    value_max = models.CharField(max_length=255, blank=True, null=True)
    current_check_date = models.DateTimeField(blank = True, null = True)
    next_check_date = models.DateTimeField(blank = True, null = True)
    sealing = models.BooleanField(default = False)
    sealing_number = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default = False, db_index = True)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.model
    
    
class FlowMeter(TimeStampedModel):
    model = models.CharField(max_length=255)
    device = models.ForeignKey(Device, on_delete = models.CASCADE, blank = True, null = True)
    modification = models.CharField(max_length=255, blank=True, null=True)
    value_min = models.CharField(max_length=255, blank=True, null=True)
    value_max = models.CharField(max_length=255, blank=True, null=True)
    current_check_date = models.DateTimeField(blank = True, null = True)
    next_check_date = models.DateTimeField(blank = True, null = True)
    sealing = models.BooleanField(default = False)
    sealing_number = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default = False, db_index = True)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.model
    
    
class MeteringPoint(TimeStampedModel):
    name = models.CharField(max_length=255)
    company_object = models.ForeignKey(CompanyObject, on_delete = models.CASCADE, blank = True, null = True)
    modem = models.ForeignKey(Modem, on_delete = models.CASCADE, blank = True, null = True)
    device = models.ForeignKey(Device, on_delete = models.CASCADE, blank = True, null = True)
    resource = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    heating_system = models.CharField(max_length=255, blank=True, null=True)
    hot_water_system = models.CharField(max_length=255, blank=True, null=True)
    tu_location = models.CharField(max_length=255, blank=True, null=True)
    input_output = models.CharField(max_length=255, blank=True, null=True)
    metering_scheme = models.CharField(max_length=255, blank=True, null=True)
    scheme_type = models.CharField(max_length=255, blank=True, null=True)
    report_template = models.CharField(max_length=255, blank=True, null=True)
    point_id = models.CharField(max_length=255, blank=True, null=True)
    point_id_additional = models.CharField(max_length=255, blank=True, null=True)
    point_id_additional1 = models.CharField(max_length=255, blank=True, null=True)
    auto_polling = models.BooleanField(default = False)
    approved_from = models.DateTimeField(blank = True, null = True)
    approved_to = models.DateTimeField(blank = True, null = True)
    device_time = models.CharField(max_length=255, blank=True, null=True)
    heat_calculation_formula = models.CharField(max_length=255, blank=True, null=True)
    transit_characteristics = models.CharField(max_length=255, blank=True, null=True)
    unloading_transit = models.CharField(max_length=255, blank=True, null=True)
    billing_from = models.DateTimeField(blank = True, null = True)
    billing_to = models.DateTimeField(blank = True, null = True)
    input_number = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for metering_point_data in MeteringPointData.objects.filter(metering_point = self):
            metering_point_data.delete()
        for task in Task.objects.filter(metering_point = self):
            task.delete()
        for obj in MeteringPointHeatSupplyScheme.objects.filter(metering_point = self):
            obj.delete()

    def __str__(self):
        return self.name
    
REPORT_TYPES = (
    (u'CURRENT', u'CURRENT'),
    (u'HOURLY', u'HOURLY'),
    (u'DAILY', u'DAILY'),
    (u'MONTHLY', u'MONTHLY'),
    (u'TOTAL', u'TOTAL'),
)
class MeteringPointData(TimeStampedModel):    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='DAILY', db_index=True)
    metering_point = models.ForeignKey(MeteringPoint, on_delete = models.CASCADE, blank = True, null = True)
    device_type = models.ForeignKey(DeviceType, on_delete = models.CASCADE, blank = True, null = True)
    timestamp = models.DateTimeField(blank = True, null = True, db_index = True)
    data = models.JSONField(blank=True, null=True)    
    all_data = models.JSONField(blank=True, null=True)    
    raw_data = models.BinaryField(blank=True, null=True)    
    calculated_data = models.JSONField(blank=True, null=True)    
    computed_data = models.JSONField(blank=True, null=True)    
    deleted = models.BooleanField(default = False, db_index = True)
    log = models.TextField(blank = True, null = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        if self.metering_point:
            return "data of point %s" % self.metering_point.name
        return self.id
    
    def calculate_data(self):
        calculated_data = []
        #T1,T2,dT, P1,P2,P, Q1,Q2, dQ
        device_type = self.device_type
        def add_value(calculated_data, data, header_names):
            index = -1
            for i in range(0, len(device_type.parameters)):
                header = device_type.parameters[i]
                if header.lower() in header_names:
                    index = i
                    break
            if index >= 0:
                if data[index]:
                    calculated_data.append(float(data[index]))
                else:
                    calculated_data.append(0.0)
            else:
                #fixme stub
                calculated_data.append(0)
        add_value(calculated_data, self.data, ["t1"])
        add_value(calculated_data, self.data, ["t2"])
        calculated_data.append(calculated_data[0] - calculated_data[1])
        add_value(calculated_data, self.data, ["p1"])
        add_value(calculated_data, self.data, ["p2"])
        calculated_data.append(calculated_data[3] - calculated_data[4])
        add_value(calculated_data, self.data, ["qо",  "qтв"])
        add_value(calculated_data, self.data, ["qг",  "q12"])
        calculated_data.append(calculated_data[6] - calculated_data[7])
        self.calculated_data = calculated_data
        computed_data = []
        for value in calculated_data:
            computed_data.append(value / 1.1)
        self.computed_data = computed_data
        self.save(update_fields = ["calculated_data", "computed_data"])
        
    def get_data_value(self, header_name):
        index = -1
        device_type = self.device_type
        for i in range(0, len(device_type.parameters)):
            header = device_type.parameters[i]
            if header.lower() == header_name.lower():
                index = i
                break
        if index >= 0:
            if isinstance(self.data[index], float):
                return "{:.2f}".format(self.data[index])
            return self.data[index]
        else:
            return "--"


class Task(TimeStampedModel):
    name = models.CharField(max_length=255)
    metering_point = models.ForeignKey(MeteringPoint, on_delete = models.CASCADE, blank = True, null = True)
    time = models.DateTimeField(blank = True, null = True, db_index = True)
    periodic_task = models.BooleanField(default = False, db_index = True)
    deleted = models.BooleanField(default = False, db_index = True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='DAILY', db_index=True)
    last_execute_time = models.DateTimeField(blank = True, null = True, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for query in Query.objects.filter(task = self):
            query.delete()

    def __str__(self):
        return self.name


REPORT_FILE_TYPES = (
    (u'PDF', u'PDF'),
    (u'XLS', u'XLS'),
    (u'CSV', u'CSV'),
    (u'DOCX', u'DOCX'),
)
PERIODIC_SEND_TYPES = (
    (u'HOURLY', u'HOURLY'),
    (u'DAILY', u'DAILY'),
    (u'MONTHLY', u'MONTHLY'),
)
class ReportTask(TimeStampedModel):
    user = models.ForeignKey(User, blank = True, null = True, on_delete = models.CASCADE, related_name = "report_task_user")
    request_user = models.ForeignKey(User, blank = True, null = True, on_delete = models.CASCADE, related_name = "report_task_request_user")
    company_objects = models.ManyToManyField(CompanyObject, blank = True)
    time = models.DateTimeField(blank = True, null = True, db_index = True)
    date_from = models.DateTimeField(blank = True, null = True, db_index = True)
    date_to = models.DateTimeField(blank = True, null = True, db_index = True)
    deleted = models.BooleanField(default = False, db_index = True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='DAILY', db_index=True)
    send_type = models.CharField(max_length=50, choices=PERIODIC_SEND_TYPES, default='DAILY', db_index=True)
    file_type = models.CharField(max_length=50, choices=REPORT_FILE_TYPES, default='PDF', db_index=True)
    last_execute_time = models.DateTimeField(blank = True, null = True, db_index = True)
    emails = models.TextField(blank = True, null = True)
    headers = models.TextField(blank = True, null = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

#     def __str__(self):
#         return self.name
    

class Query(TimeStampedModel):    
    name = models.CharField(max_length=255)
    task = models.ForeignKey(Task, on_delete = models.CASCADE, blank = True, null = True)
    request_time = models.DateTimeField(blank = True, null = True)
    response_time = models.DateTimeField(blank = True, null = True)
    request = models.TextField(blank = True, null = True)
    response = models.TextField(blank = True, null = True)
    error = models.BooleanField(default = False)
    deleted = models.BooleanField(default = False, db_index = True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.name
    

class Department(TimeStampedModel):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete = models.CASCADE, blank = True, null = True)
    deleted = models.BooleanField(default = False, db_index = True)
    parent_department = models.ForeignKey('self', on_delete = models.CASCADE, blank = True, null = True)
    department_type = models.CharField(max_length=255, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for department in Department.objects.filter(parent_department = self):
            department.delete()

    def __str__(self):
        return self.name


class DepartmentType(TimeStampedModel):
    name = models.CharField(max_length=255)
    deleted = models.BooleanField(default = False, db_index = True)
    role = models.CharField(max_length=256, blank=True, null=True)
    
    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.name


DATA_EDIT_ACTIONS = (
    (u'Add', u'Add'),
    (u'Edit', u'Edit'),
    (u'Delete', u'Delete'),
)
class DataEditHistory(TimeStampedModel):
    user = models.ForeignKey(User, on_delete = models.CASCADE, blank = True, null = True)
    action = models.CharField(max_length=50, choices=DATA_EDIT_ACTIONS, null=True, blank=True, db_index=True)
    model_name = models.CharField(max_length=255)
    object_id = models.BigIntegerField()
    object_name = models.CharField(max_length=255, blank = True, null = True)
    data = models.JSONField(blank=True, null=True) 

    class Meta:
        verbose_name = "Data edit history"
        verbose_name_plural = "Data edit history"
        

class HeatSupplyScheme(TimeStampedModel):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete = models.CASCADE, blank = True, null = True)
    deleted = models.BooleanField(default = False, db_index = True)
    data = models.JSONField(blank=True, null=True)    

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
        #deleting dependences
        for obj in MeteringPointHeatSupplyScheme.objects.filter(heat_supply_scheme = self):
            obj.delete()

    def __str__(self):
        return self.name


class MeteringPointHeatSupplyScheme(TimeStampedModel):
    metering_point = models.ForeignKey(MeteringPoint, on_delete = models.CASCADE, blank = True, null = True)    
    heat_supply_scheme = models.ForeignKey(HeatSupplyScheme, on_delete = models.CASCADE, blank = True, null = True)
    parameters = models.JSONField(blank=True, null=True)    
    deleted = models.BooleanField(default = False, db_index = True)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()

    def __str__(self):
        return "metering point %s data for heat supply scheme %s" % (self.metering_point, self.heat_supply_scheme)
        