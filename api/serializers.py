from rest_framework.serializers import ModelSerializer, Serializer
from heatcontrol.api.models import User, Company, CompanyObject, Device, Modem,\
    Task, Query, MeteringPoint, DeviceType, MeteringPointData, UserPermissions,\
    Department, ModemType, HeatSupplyScheme, MeteringPointHeatSupplyScheme,\
    CompanyObjectWeatherData, DepartmentType, SensorType, FlowMeterType, Sensor,\
    FlowMeter
from rest_framework import serializers


class CompanySerializer(ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', "name", "address", "address_coords", "company_type", "fias_code", "phone", 'fax', 'inn', 'email', "parent_company_id", "created_date", "tariff", "departments", "tags", "timezone", 'created')

    def to_representation(self, instance):
        data = ModelSerializer.to_representation(self, instance)
        data["objects_count"] = CompanyObject.objects.filter(company = instance, deleted = False).count()
        data["devices_count"] = Device.objects.filter(company_object__company = instance, deleted = False).count()
        data["employee_count"] = User.objects.filter(employer = instance, deleted = False).count()
        data["modems_count"] = Modem.objects.filter(company_object__company = instance, deleted = False).count()
        if instance.logo:
            data["logo"] = instance.logo.url
        else:
            data["logo"] = None
        if instance.parent_company_id:
            parent_company = Company.objects.filter(id = instance.parent_company_id)[:1]
            if parent_company.count():
                data["parent_company_name"] = parent_company[0].name
            else:
                data["parent_company_name"] = None
        else:
            data["parent_company_name"] = None
        return data

    def create(self, validated_data):
        company = Company.objects.create(**validated_data)
        company.save()        
        return company
        

class CompaniesNamesSerializer(ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', "name")


class DepartmentTypeSerializer(ModelSerializer):        
    class Meta:
        model = DepartmentType
        fields = ('id', "name", "role")

    def create(self, validated_data):
        department_type = DepartmentType.objects.create(**validated_data)
        department_type.save()
        return department_type
        
        
class DepartmentSerializer(ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', "name", "department_type")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.company:
            data["company_id"] = instance.company.id
            data["company_name"] = instance.company.name
        if instance.parent_department:
            data["parent"] = instance.parent_department.id
        return data

    def create(self, validated_data):
        department = Department.objects.create(**validated_data)
        department.save()
        if "company_id" in self.initial_data:
            company = Company.objects.filter(id = self.initial_data["company_id"])
            if company.count():
                department.company = company[0]        
                department.save(update_fields = ["company"])
        if "parent" in self.initial_data:
            parent = Department.objects.filter(id = self.initial_data["parent"])
            if parent.count():
                department.parent_department = parent[0]        
                department.save(update_fields = ["parent_department"])
        return department

    
    def update(self, instance, validated_data):
        if 'company_id' in validated_data:
            company = Company.objects.filter(id = validated_data["company_id"])
            if company.count():
                instance.company = company[0]        
        if 'parent' in validated_data:
            parent = Department.objects.filter(id = validated_data["parent"])
            if parent.count():
                instance.parent_department = parent[0]        
        return ModelSerializer.update(self, instance, validated_data)


class CompanyObjectSerializer(ModelSerializer):        
    class Meta:
        model = CompanyObject
        fields = ('id', "name", "address", "address_coords", 'move_resource', "object_type", "mode", 'mode_switch_date', 'timezone', 'fias', "note", "tags", 'created', "t1_min", "t1_max", "t2_min", "t2_max", "dt_min", "dt_max", "p1_min", "p1_max", "p2_min", "p2_max", "dp_min", "dp_max", "q1_min", "q1_max", "q2_min", "q2_max", "dq_min", "dq_max", "heating_season_start_date", 'heating_season_enabled_date', 'object_category')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.company:
            data["company_id"] = instance.company.id
            data["company_name"] = instance.company.name
        weathers = CompanyObjectWeatherData.objects.filter(company_object = instance).order_by("-created")[:1]
        if weathers.count():
            weather = weathers[0]
            data["weather"] = CompanyObjectWeatherDataSerializer(weather).data
        return data

    def create(self, validated_data):
        company_object = CompanyObject.objects.create(**validated_data)
        company_object.save()
        if "company_id" in self.initial_data:
            company = Company.objects.filter(id = self.initial_data["company_id"])
            if company.count():
                company_object.company = company[0]        
                company_object.save(update_fields = ["company"])
        return company_object

    
    def update(self, instance, validated_data):
        if 'company_id' in validated_data:
            company = Company.objects.filter(id = validated_data["company_id"])
            if company.count():
                instance.company = company[0]        
        return ModelSerializer.update(self, instance, validated_data)


class CompanyObjectWeatherDataSerializer(ModelSerializer):
    class Meta:
        model = CompanyObjectWeatherData
        fields = ('id', "created")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.data:
            json = instance.data
            if "list" in json:
                weather_data = json["list"][0]
                data["timestamp"] = weather_data["dt"]
                if "main" in weather_data:
                    data["temp"] = weather_data["main"]["temp"]
                    data["feels_like"] = weather_data["main"]["feels_like"]
                    data["temp_min"] = weather_data["main"]["temp_min"]
                    data["pressure"] = weather_data["main"]["pressure"]
                    data["sea_level"] = weather_data["main"]["sea_level"]
                    data["grnd_level"] = weather_data["main"]["grnd_level"]
                    data["humidity"] = weather_data["main"]["humidity"]
                if "weather" in weather_data and len(weather_data["weather"]) > 0:
                    data["main"] = weather_data["weather"][0]["main"]
                    data["description"] = weather_data["weather"][0]["description"]
                    data["icon"] = weather_data["weather"][0]["icon"]
                if "clouds" in weather_data and "all" in weather_data["clouds"]:
                    data["clouds"] = weather_data["clouds"]["all"]
                if "wind" in weather_data:
                    data["wind_speed"] = weather_data["wind"]["speed"]
                    data["wind_deg"] = weather_data["wind"]["deg"]
                data["visibility"] = weather_data["visibility"]
                if "rain" in weather_data:
                    data["rain"] = weather_data["rain"]["3h"]
                if "snow" in weather_data:
                    data["snow"] = weather_data["snow"]["3h"]
        return data

    
    
class DeviceTypeSerializer(ModelSerializer):        
    class Meta:
        model = DeviceType
        fields = ('id', "name", "vendor", "model", "parameters", "parameter_units", "current_report_parameters", "current_report_parameter_units", "template_pdf", "template_xls", "template_docx")

    def create(self, validated_data):
        device_type = DeviceType.objects.create(**validated_data)
        device_type.save()
        return device_type


class ModemTypeSerializer(ModelSerializer):        
    class Meta:
        model = ModemType
        fields = ('id', "name")

    def create(self, validated_data):
        modem_type = ModemType.objects.create(**validated_data)
        modem_type.save()
        return modem_type


class SensorTypeSerializer(ModelSerializer):        
    class Meta:
        model = SensorType
        fields = ('id', "name")

    def create(self, validated_data):
        sensor_type = SensorType.objects.create(**validated_data)
        sensor_type.save()
        return sensor_type


class FlowMeterTypeSerializer(ModelSerializer):        
    class Meta:
        model = FlowMeterType
        fields = ('id', "name")

    def create(self, validated_data):
        flow_meter_type = FlowMeterType.objects.create(**validated_data)
        flow_meter_type.save()
        return flow_meter_type
    
    
class DeviceSerializer(ModelSerializer):        
    class Meta:
        model = Device
        fields = ('id', "name", "serial_number", "network_address", "modification", "speed", 'service_company', 'data_format', 'channel', "driver_version", "current_check_date", "next_check_date", "sealing_date", "device_time", "gis_number", "device_id", "accounting_type", "owner", "notes", "parameters", 'created', "status", "sensors", "flow_meters", "status_changed_date", "connection_string")
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["name"] = instance.__str__()
        if instance.company_object:
            data["company_object_id"] = instance.company_object.id
            data["company_object_name"] = instance.company_object.name
            if instance.company_object.company:
                data["company_id"] = instance.company_object.company.id
                data["company_name"] = instance.company_object.company.name
        if instance.modem:
            data["modem_id"] = instance.modem.id
            data["modem_model"] = instance.modem.model
        if instance.device_type:
            data["device_type_id"] = instance.device_type.id
            data["device_type_name"] = instance.device_type.name
        return data

    def create(self, validated_data):
#         print(self.initial_data)
        device = Device.objects.create(**validated_data)
        device.save()
        if "device_type_id" in self.initial_data:
#             print("found device_type_id: %s" % validated_data["device_type_id"])
            device_type = DeviceType.objects.filter(id = self.initial_data["device_type_id"])
            if device_type.count():
                device.device_type = device_type[0]        
                device.save(update_fields = ["device_type"])
        if "company_object_id" in self.initial_data:
            company_object = CompanyObject.objects.filter(id = self.initial_data["company_object_id"])
            if company_object.count():
                device.company_object = company_object[0]        
                device.save(update_fields = ["company_object"])
        if "modem_id" in self.initial_data:
            modems = Modem.objects.filter(id = self.initial_data["modem_id"])[:1]
            if modems.count():
                modem = modems[0]
                device.modem = modem
                device.save(update_fields = ["modem"])
        return device

    
    def update(self, instance, validated_data):
        if 'company_object_id' in validated_data:
            company_object = CompanyObject.objects.filter(id = validated_data["company_object_id"])
            if company_object.count():
                instance.company_object = company_object[0]        
        if "modem_id" in validated_data:
            modems = Modem.objects.filter(id = validated_data["modem_id"])[:1]
            if modems.count():
                modem = modems[0]
                instance.modem = modem
        if "device_type_id" in validated_data:
            device_type = DeviceType.objects.filter(id = validated_data["device_type_id"])
            if device_type.count():
                instance.device_type = device_type[0]        
        return ModelSerializer.update(self, instance, validated_data)


class ModemSerializer(ModelSerializer):        
    class Meta:
        model = Modem
        fields = ('id', "model", "serial_number", "phone", "auto_off", "apn", 'speed_code1', 'speed_code2', 'speed_code3', "allow_connection", "connection_string", "edge_enabled", "firmware_version", "gps_class", "gprs_setings_setup", "sim_identifier", "device_identifier", "interface_code1", "interface_code2", "interface_code3", "login", "password", "operator", "signal_level", "sms_center", "imei", "active", "mac_address", 'created')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.company_object:
            data["company_object_id"] = instance.company_object.id
            data["company_object_name"] = instance.company_object.name
            if instance.company_object.company:
                data["company_id"] = instance.company_object.company.id
                data["company_name"] = instance.company_object.company.name
        return data

    def create(self, validated_data):
        modem = Modem.objects.create(**validated_data)
        modem.save()
        if "company_object_id" in self.initial_data:
            company_object = CompanyObject.objects.filter(id = self.initial_data["company_object_id"])
            if company_object.count():
                modem.company_object = company_object[0]        
                modem.save(update_fields = ["company_object"])
        return modem

    
    def update(self, instance, validated_data):
        if 'company_object_id' in validated_data:
            company_object = CompanyObject.objects.filter(id = validated_data["company_object_id"])
            if company_object.count():
                instance.company_object = company_object[0]        
        return ModelSerializer.update(self, instance, validated_data)


class SensorSerializer(ModelSerializer):        
    class Meta:
        model = Sensor
        fields = ('id', "model", "modification", "value_min", "value_max", "current_check_date", "next_check_date", "sealing", "sealing_number")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.device:
            data["device_id"] = instance.device.id
        return data

    def create(self, validated_data):
        sensor = Sensor.objects.create(**validated_data)
        sensor.save()
        if "device_id" in self.initial_data:
            device = Device.objects.filter(id = self.initial_data["device_id"])
            if device.count():
                sensor.device = device[0]        
                sensor.save(update_fields = ["device"])
        return sensor

    def update(self, instance, validated_data):
        if "device_id" in validated_data:
            device = Device.objects.filter(id = validated_data["device_id"])
            if device.count():
                instance.device = device[0]        
        return ModelSerializer.update(self, instance, validated_data)
    
    
class FlowMeterSerializer(ModelSerializer):        
    class Meta:
        model = FlowMeter
        fields = ('id', "model", "modification", "value_min", "value_max", "current_check_date", "next_check_date", "sealing", "sealing_number")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.device:
            data["device_id"] = instance.device.id
        return data

    def create(self, validated_data):
        sensor = FlowMeter.objects.create(**validated_data)
        sensor.save()
        if "device_id" in self.initial_data:
            device = Device.objects.filter(id = self.initial_data["device_id"])
            if device.count():
                sensor.device = device[0]        
                sensor.save(update_fields = ["device"])
        return sensor

    def update(self, instance, validated_data):
        if "device_id" in validated_data:
            device = Device.objects.filter(id = validated_data["device_id"])
            if device.count():
                instance.device = device[0]        
        return ModelSerializer.update(self, instance, validated_data)
    
    
class TaskSerializer(ModelSerializer):        
    class Meta:
        model = Task
        fields = ('id', "name", "time", "periodic_task", "report_type")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.metering_point:
            data["metering_point_id"] = instance.metering_point.id
            data["metering_point_name"] = instance.metering_point.name
        return data

    def create(self, validated_data):
        task = Task.objects.create(**validated_data)
        task.save()
        if "metering_point_id" in self.initial_data:
            metering_point = MeteringPoint.objects.filter(id = self.initial_data["metering_point_id"])
            if metering_point.count():
                task.metering_point = metering_point[0]        
                task.save(update_fields = ["metering_point"])
        return task

    
    def update(self, instance, validated_data):
        if "metering_point_id" in validated_data:
            metering_point = MeteringPoint.objects.filter(id = validated_data["metering_point_id"])
            if metering_point.count():
                instance.metering_point = metering_point[0]        
        return ModelSerializer.update(self, instance, validated_data)
    
    
class QuerySerializer(ModelSerializer):        
    class Meta:
        model = Query
        fields = ('id', "name", "request_time", "response_time", 'request', 'response', 'error')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.task:
            data["task_id"] = instance.task.id
            data["task_name"] = instance.task.name
        return data

    def create(self, validated_data):
        query = Query.objects.create(**validated_data)
        query.save()
        if "task_id" in self.initial_data:
            task = Task.objects.filter(id = self.initial_data["task_id"])
            if task.count():
                query.task = task[0]        
                query.save(update_fields = ["task"])
        return query

    
    def update(self, instance, validated_data):
        if 'task_id' in validated_data:
            task = Task.objects.filter(id = validated_data["task_id"])
            if task.count():
                instance.task = task[0]        
        return ModelSerializer.update(self, instance, validated_data)


class UserCompanySerializer(ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', "name")

    def to_representation(self, instance):
        data = ModelSerializer.to_representation(self, instance)
        if instance.logo:
            data["logo"] = instance.logo.url
        return data


class UserPermissionsSerializer(ModelSerializer):
    class Meta:
        model = UserPermissions
        fields = ('id', 'role', 'status_admin_system', 'status_admin_company', 'status_admin_company_object', "status_admin_modem", "status_admin_device")


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'patronymic',
                  "phone", 'department', "role", "position")
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.employer:
            data["company"] = UserCompanySerializer(instance.employer).data
        else:
            data["company"] = None
        data["register_date"] = instance.date_joined
        if instance.avatar:
            data["avatar"] = instance.avatar.url
        permissions = instance.get_permissions()
        if permissions:
            data["permissions"] = UserPermissionsSerializer(permissions).data
        else:
            data["permissions"] = None
        return data
    
    def update(self, instance, validated_data):
        if 'company_id' in validated_data:
            company = Company.objects.filter(id = validated_data["company_id"])
            if company.count():
                instance.employer = company[0]        
        return ModelSerializer.update(self, instance, validated_data)
            
        
class CreateUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'patronymic',
                  'phone', 'department', 'password', "role", "position")
        extra_kwargs = {'password': {'write_only': True}}
        
    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['email'],
                                        validated_data['password'])
        if 'first_name' in validated_data:
            user.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            user.last_name = validated_data['last_name']
        if 'patronymic' in validated_data:
            user.patronymic = validated_data['patronymic']
        if 'phone' in validated_data:
            user.phone = validated_data['phone']
        if 'company_id' in validated_data:
            company = Company.objects.filter(id = validated_data["company_id"])
            if company.count():
                user.employer = company[0]
        if 'department' in validated_data:
            user.department = validated_data['department']
        if 'role' in validated_data:
            user.role = validated_data['role']
        if 'position' in validated_data:
            user.position = validated_data['position']
        user.save()
        return user


class TotalsSerializer(Serializer):
    companies = serializers.IntegerField()
    users = serializers.IntegerField()
    company_objects = serializers.IntegerField()
    modems = serializers.IntegerField()
    active_modems = serializers.IntegerField()
    inactive_modems = serializers.IntegerField()
    devices = serializers.IntegerField()
    

class MeteringPointSerializer(ModelSerializer):
    class Meta:
        model = MeteringPoint
        fields = ('id', "name", "resource", "destination", "heating_system", "hot_water_system", 'tu_location', 'input_output', 'metering_scheme', "scheme_type", "report_template", "point_id", "point_id_additional", "point_id_additional1", "auto_polling", "approved_from", "approved_to", "device_time", "heat_calculation_formula", "transit_characteristics", "unloading_transit", "billing_from", "billing_to", "input_number", "notes", 'created')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.company_object:
            data["company_object_id"] = instance.company_object.id
            data["company_object_name"] = instance.company_object.name
            if instance.company_object.company:
                data["company_id"] = instance.company_object.company.id
                data["company_name"] = instance.company_object.company.name
        if instance.modem:
            data["modem_id"] = instance.modem.id
            data["modem_model"] = instance.modem.model
        if instance.device:
            data["device_id"] = instance.device.id
            data["device_name"] = instance.device.__str__()
        return data

    def create(self, validated_data):
        metering_point = MeteringPoint.objects.create(**validated_data)
        metering_point.save()
        if "company_object_id" in self.initial_data:
            company_object = CompanyObject.objects.filter(id = self.initial_data["company_object_id"])
            if company_object.count():
                metering_point.company_object = company_object[0]        
                metering_point.save(update_fields = ["company_object"])
        if "modem_id" in self.initial_data:
            modem = Modem.objects.filter(id = self.initial_data["modem_id"])
            if modem.count():
                metering_point.modem = modem[0]        
                metering_point.save(update_fields = ["modem"])
        if "device_id" in self.initial_data:
            device = Device.objects.filter(id = self.initial_data["device_id"])
            if device.count():
                metering_point.device = device[0]        
                metering_point.save(update_fields = ["device"])
        return metering_point

    
    def update(self, instance, validated_data):
        if 'company_object_id' in validated_data:
            company_object = CompanyObject.objects.filter(id = validated_data["company_object_id"])
            if company_object.count():
                instance.company_object = company_object[0]        
        if "modem_id" in validated_data:
            modem = Modem.objects.filter(id = validated_data["modem_id"])
            if modem.count():
                instance.modem = modem[0]        
        if "device_id" in validated_data:
            device = Device.objects.filter(id = validated_data["device_id"])
            if device.count():
                instance.device = device[0]        
        return ModelSerializer.update(self, instance, validated_data)
    
    
class MeteringPointDataSerializer(ModelSerializer):
    class Meta:
        model = MeteringPointData
        fields = ('id', "timestamp", "data", "log", "calculated_data", "report_type", "computed_data", "all_data")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.metering_point:
            data["metering_point_id"] = instance.metering_point.id
            data["metering_point_name"] = instance.metering_point.name
        if instance.device_type:
            data["device_type_id"] = instance.device_type.id
            data["device_type_name"] = instance.device_type.name
        if instance.raw_data:
            raw_data = bytes(instance.raw_data)
            str = ""
            for byte in raw_data:
                str += hex(byte)
                str += " "
            data["raw_data"] = str
        return data


    def create(self, validated_data):
        metering_point_data = MeteringPointData.objects.create(**validated_data)
        metering_point_data.save()
        if "metering_point_id" in self.initial_data:
            metering_point = MeteringPoint.objects.filter(id = self.initial_data["metering_point_id"])
            if metering_point.count():
                metering_point_data.metering_point = metering_point[0]        
                metering_point_data.save(update_fields = ["metering_point"])
        if "device_type_id" in self.initial_data:
            device_type = DeviceType.objects.filter(id = self.initial_data["device_type_id"])
            if device_type.count():
                metering_point_data.device_type = device_type[0]        
                metering_point_data.save(update_fields = ["device_type"])
        return metering_point_data

    
    def update(self, instance, validated_data):
#         print(validated_data)
        if "metering_point_id" in validated_data:
            metering_point = MeteringPoint.objects.filter(id = validated_data["metering_point_id"])
            if metering_point.count():
                instance.metering_point = metering_point[0]        
        if "device_type_id" in validated_data:
            device_type = DeviceType.objects.filter(id = validated_data["device_type_id"])
            if device_type.count():
                instance.device_type = device_type[0]        
        return ModelSerializer.update(self, instance, validated_data)


class FiasDataSerializer(Serializer):
    address = serializers.CharField()
    address_coords = serializers.ListField(child = serializers.FloatField())


class AddressSuggestionDataSerializer(Serializer):
    address = serializers.CharField()
    fias_code = serializers.CharField()
    timezone = serializers.CharField()
    address_coords = serializers.ListField(child = serializers.FloatField())


class HeatSupplySchemeSerializer(ModelSerializer):
    class Meta:
        model = HeatSupplyScheme
        fields = ('id', "name", "created", "data")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.user:
            data["user_id"] = instance.user.id
        return data


    def create(self, validated_data):
        obj = HeatSupplyScheme.objects.create(**validated_data)
        obj.save()
        if "user_id" in self.initial_data:
            user = User.objects.filter(id = self.initial_data["user_id"])
            if user.count():
                obj.user = user[0]        
                obj.save(update_fields = ["user"])
        return obj

    
    def update(self, instance, validated_data):
#         print(validated_data)
        if "user_id" in validated_data:
            user = User.objects.filter(id = validated_data["user_id"])
            if user.count():
                instance.user = user[0]        
        return ModelSerializer.update(self, instance, validated_data)


class MeteringPointHeatSupplySchemeSerializer(ModelSerializer):
    class Meta:
        model = MeteringPointHeatSupplyScheme
        fields = ('id', "created", "parameters")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.metering_point:
            data["metering_point_id"] = instance.metering_point.id
        if instance.heat_supply_scheme:
            data["heat_supply_scheme_id"] = instance.heat_supply_scheme.id
        return data


    def create(self, validated_data):
        obj = MeteringPointHeatSupplyScheme.objects.create(**validated_data)
        obj.save()
        if "metering_point_id" in self.initial_data:
            metering_point = MeteringPoint.objects.filter(id = self.initial_data["metering_point_id"])
            if metering_point.count():
                obj.metering_point = metering_point[0]        
                obj.save(update_fields = ["metering_point"])
        if "heat_supply_scheme_id" in self.initial_data:
            heat_supply_scheme = HeatSupplyScheme.objects.filter(id = self.initial_data["heat_supply_scheme_id"])
            if heat_supply_scheme.count():
                obj.heat_supply_scheme = heat_supply_scheme[0]        
                obj.save(update_fields = ["heat_supply_scheme"])
        return obj

    
    def update(self, instance, validated_data):
#         print(validated_data)
        if "metering_point_id" in validated_data:
            metering_point = MeteringPoint.objects.filter(id = validated_data["metering_point_id"])
            if metering_point.count():
                instance.metering_point = metering_point[0]        
        if "heat_supply_scheme_id" in validated_data:
            heat_supply_scheme = HeatSupplyScheme.objects.filter(id = validated_data["heat_supply_scheme_id"])
            if heat_supply_scheme.count():
                instance.heat_supply_scheme = heat_supply_scheme[0]        
        return ModelSerializer.update(self, instance, validated_data)


class SearchResultSerializer(Serializer):
    users = serializers.ListField(child = UserSerializer())
    companies = serializers.ListField(child = CompanySerializer())
    company_objects = serializers.ListField(child = CompanyObjectSerializer())
    metering_points = serializers.ListField(child = MeteringPointSerializer())
    modems = serializers.ListField(child = ModemSerializer())
    devices = serializers.ListField(child = DeviceSerializer())


class ReportSerializer(Serializer):
    headers = serializers.JSONField()
    values = serializers.ListField(child = MeteringPointDataSerializer())
    

class CompanyObjectDeviceDataSerializer(Serializer):
    object = CompanyObjectSerializer()
    last_hour_datas = serializers.ListField(child = MeteringPointDataSerializer()) 
      