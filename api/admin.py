from django.contrib import admin
from heatcontrol.api.models import User, Company, CompanyObject, Device, Modem,\
    Task, Query, MeteringPoint, DeviceType, MeteringPointData, UserPermissions,\
    Department, DataEditHistory, ModemType, HeatSupplyScheme,\
    CompanyObjectWeatherData, MeteringPointHeatSupplyScheme, DepartmentType,\
    ReportTask, SensorType, FlowMeterType, Sensor, FlowMeter, BusyDevice
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.options import ModelAdmin

# Register your models here.
@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("id", 'username', 'email', 'first_name', 'last_name', 'is_staff', "deleted")
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]["fields"] = ('first_name', "patronymic", 'last_name', 'email', "employer", "department", "position", "role", "avatar", "deleted")
    raw_id_fields = ('employer', )


class DepartmentInline(admin.TabularInline):
    model = Department
#     raw_id_fields = ('parent', )
    extra = 0


class DepartmentTypeAdmin(ModelAdmin):
    list_display = ("id", 'name', "role", "deleted")


class CompanyAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")
    inlines = [DepartmentInline]
    

class CompanyObjectAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class CompanyObjectWeatherDataAdmin(ModelAdmin):
    list_display = ("created", 'company_object')


class DeviceAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class BusyDeviceAdmin(ModelAdmin):
    list_display = ("created", 'device')
    raw_id_fields = ('device', )


class ModemAdmin(ModelAdmin):
    list_display = ("id", 'model', "deleted")


class SensorAdmin(ModelAdmin):
    list_display = ("id", 'model', "deleted")


class FlowMeterAdmin(ModelAdmin):
    list_display = ("id", 'model', "deleted")


class TaskAdmin(ModelAdmin):
    list_display = ("id", 'name', "periodic_task", "report_type", "last_execute_time", "deleted")


class ReportTaskAdmin(ModelAdmin):
    list_display = ("id", 'user', "send_type", "last_execute_time", "deleted")


class QueryAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class MeteringPointAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class DeviceTypeAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class ModemTypeAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class SensorTypeAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")


class FlowMeterTypeAdmin(ModelAdmin):
    list_display = ("id", 'name', "deleted")

    
class MeteringPointDataAdmin(ModelAdmin):
    list_display = ("timestamp", "metering_point", "deleted")
    change_form_template = "admin/metering_point_data_change_form.html"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            metering_point_data = MeteringPointData.objects.get(id = object_id)
            extra_context["metering_point_data"] = metering_point_data
            if metering_point_data.raw_data:
                data = bytes(metering_point_data.raw_data)
                str = ""
                for byte in data:
                    str += hex(byte)
                    str += " "
                extra_context["raw_data"] = str
        return super(MeteringPointDataAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
    

class DataEditHistoryAdmin(ModelAdmin):
    list_display = ("created", "action", "user", "model_name", "object_id", "object_name")
    raw_id_fields = ('user', )


class HeatSupplySchemeAdmin(ModelAdmin):
    list_display = ("id", 'name', "user", "created", "deleted")


class MeteringPointHeatSupplySchemeAdmin(ModelAdmin):
    list_display = ("id", 'metering_point', "heat_supply_scheme", "deleted")
    

admin.site.register(UserPermissions)
admin.site.register(Company, CompanyAdmin)
admin.site.register(CompanyObject, CompanyObjectAdmin)
admin.site.register(CompanyObjectWeatherData, CompanyObjectWeatherDataAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(BusyDevice, BusyDeviceAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(FlowMeter, FlowMeterAdmin)
admin.site.register(Modem, ModemAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(ReportTask, ReportTaskAdmin)
admin.site.register(Query, QueryAdmin)
admin.site.register(MeteringPoint, MeteringPointAdmin)
admin.site.register(DeviceType, DeviceTypeAdmin)
admin.site.register(ModemType, ModemTypeAdmin)
admin.site.register(SensorType, SensorTypeAdmin)
admin.site.register(FlowMeterType, FlowMeterTypeAdmin)
admin.site.register(MeteringPointData, MeteringPointDataAdmin)
admin.site.register(DataEditHistory, DataEditHistoryAdmin)
admin.site.register(HeatSupplyScheme, HeatSupplySchemeAdmin)
admin.site.register(MeteringPointHeatSupplyScheme, MeteringPointHeatSupplySchemeAdmin)
admin.site.register(DepartmentType, DepartmentTypeAdmin)
