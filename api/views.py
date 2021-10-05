from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from heatcontrol.api.serializers import UserSerializer, CreateUserSerializer,\
    CompaniesNamesSerializer, CompanySerializer, CompanyObjectSerializer,\
    DeviceSerializer, ModemSerializer, TaskSerializer, QuerySerializer,\
    TotalsSerializer, MeteringPointSerializer, DeviceTypeSerializer,\
    MeteringPointDataSerializer, UserPermissionsSerializer, DepartmentSerializer,\
    FiasDataSerializer, ModemTypeSerializer, AddressSuggestionDataSerializer,\
    HeatSupplySchemeSerializer, SearchResultSerializer,\
    MeteringPointHeatSupplySchemeSerializer, ReportSerializer,\
    CompanyObjectWeatherDataSerializer, DepartmentTypeSerializer,\
    CompanyObjectDeviceDataSerializer, SensorTypeSerializer,\
    FlowMeterTypeSerializer, SensorSerializer, FlowMeterSerializer
from rest_framework.authtoken.models import Token
from heatcontrol.api.models import Company, User, CompanyObject, Device, Modem,\
    Task, Query, MeteringPoint, DeviceType, MeteringPointData, UserPermissions,\
    Department, ModemType, HeatSupplyScheme, MeteringPointHeatSupplyScheme,\
    CompanyObjectWeatherData, DepartmentType, ReportTask, SensorType,\
    FlowMeterType, Sensor, FlowMeter, BusyDevice
from django.http.response import Http404, HttpResponseForbidden, HttpResponse
from heatcontrol.api.forms import ImageUploadForm
from django.views.decorators.csrf import csrf_exempt
from heatcontrol.api.utils import send_email, track_object_updated,\
    generate_report, set_user_role, check_mock_reports,\
    generate_separate_objects_report, create_docx_report, create_pdf_report
from django.conf import settings
from heatcontrol.api.permissions import CompanyAdminPermission,\
    DeviceAdminPermission, SystemAdminPermission, CompanyObjectAdminPermission,\
    ModemAdminPermission, check_company_permission,\
    check_company_object_permission, check_device_permission,\
    check_modem_permission, check_user_permission
from django.utils import dateparse
import requests
from watson import search as watson
import json
from django.template.response import TemplateResponse
from django.template import loader
from pathlib import Path
import mimetypes
from random import randint
import csv
from django.core.mail.message import EmailMessage
import traceback
from heatcontrol.devices.utils import get_device_obj
from heatcontrol.api.management.commands.create_xlsx import create_excel_report
import time
from rest_framework.status import HTTP_503_SERVICE_UNAVAILABLE


# Create your views here.
class AuthCheckView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        user = request.user
        content = {
            'auth': 'success',
            'user': UserSerializer(user).data,
        }
        return Response(content)
    
    
class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.deleted:
            return HttpResponseForbidden("user is deleted")
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
        })


class RegistrationView(APIView):
    def post(self, request, *args, **kwargs):
#         print(request.data)
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if "company_id" in request.data:
            company = Company.objects.filter(id = request.data["company_id"])[:1]
            if company.count():
                user.employer = company[0]
                user.save(update_fields = ["employer"])
        track_object_updated("Add", None, user, user.username, None)
        token, created = Token.objects.get_or_create(user=user)
        set_user_role(user)
        password = request.data["password"]
        send_email(
            user.email,
            "email/user_registered_subject.html",
            "email/user_registered.html",
            user = user,
            password = password,
            use_html = True,
        )
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
        })


class UserView(APIView):
    permission_classes = (IsAuthenticated,)            

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        user = User.objects.filter(id = user_id, deleted = False)[:1]
        if not user.count():
            raise Http404
        user = user[0]
        check_user_permission(request.user, user, read_access = True)
        return Response(UserSerializer(user).data)

    def post(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        user = User.objects.filter(id = user_id, deleted = False)[:1]
        if not user.count():
            raise Http404
        user = user[0]
        check_user_permission(request.user, user)
        serializer = UserSerializer(user)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, user, user.username, request.data)
        serializer.update(user, request.data)
        set_user_role(user)
        return Response(UserSerializer(user).data)
    
    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        user = User.objects.filter(id = user_id, deleted = False)
        if not user.count():
            raise Http404
        check_user_permission(request.user, user)
        track_object_updated("Delete", request.user, user[0], user[0].username, None)
        user[0].delete()
        return Response("ok")
    

class CompaniesNamesView(APIView):
    def get(self, request):
        return Response(CompaniesNamesSerializer(Company.objects.filter(deleted = False).order_by("name"), many = True).data)


class DeviceTypesView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        return Response(DeviceTypeSerializer(DeviceType.objects.filter(deleted = False).order_by("name"), many = True).data)

class AddDEviceTypeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = DeviceTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_type = serializer.save()
        track_object_updated("Add", request.user, device_type, device_type.name, None)
        return Response(DeviceTypeSerializer(device_type).data)


class DeviceTypeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_type_id = kwargs.get("device_type_id")
        device_type = DeviceType.objects.filter(id = device_type_id, deleted = False)[:1]
        if not device_type.count():
            raise Http404
        device_type = device_type[0]
        return Response(DeviceTypeSerializer(device_type).data)

    def post(self, request, *args, **kwargs):
        device_type_id = kwargs.get("device_type_id")
        device_type = DeviceType.objects.filter(id = device_type_id, deleted = False)[:1]
        if not device_type.count():
            raise Http404
        device_type = device_type[0]
        serializer = DeviceTypeSerializer(device_type)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, device_type, device_type.name, request.data)
        serializer.update(device_type, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        device_type_id = kwargs.get("device_type_id")
        device_type = DeviceType.objects.filter(id = device_type_id, deleted = False)
        if not device_type.count():
            raise Http404
        track_object_updated("Delete", request.user, device_type[0], device_type[0].name, None)
        device_type[0].delete()
        return Response("ok")
    
    
class ModemTypesView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        return Response(ModemTypeSerializer(ModemType.objects.filter(deleted = False).order_by("name"), many = True).data)


class AddModemTypeView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission) 

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ModemTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        modem_type = serializer.save()
        track_object_updated("Add", request.user, modem_type, modem_type.name, None)
        return Response(ModemTypeSerializer(modem_type).data)


class ModemTypeView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        modem_type_id = kwargs.get("modem_type_id")
        modem_type = ModemType.objects.filter(id = modem_type_id, deleted = False)[:1]
        if not modem_type.count():
            raise Http404
        modem_type = modem_type[0]
        return Response(ModemTypeSerializer(modem_type).data)

    def post(self, request, *args, **kwargs):
        modem_type_id = kwargs.get("modem_type_id")
        modem_type = ModemType.objects.filter(id = modem_type_id, deleted = False)[:1]
        if not modem_type.count():
            raise Http404
        modem_type = modem_type[0]
        serializer = ModemTypeSerializer(modem_type)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, modem_type, modem_type.name, request.data)
        serializer.update(modem_type, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        modem_type_id = kwargs.get("modem_type_id")
        modem_type = ModemType.objects.filter(id = modem_type_id, deleted = False)[:1]
        if not modem_type.count():
            raise Http404
        track_object_updated("Delete", request.user, modem_type[0], modem_type[0].name, None)
        modem_type[0].delete()
        return Response("ok")
    
    
class SensorTypesView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        return Response(SensorTypeSerializer(SensorType.objects.filter(deleted = False).order_by("name"), many = True).data)


class AddSensorTypeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = SensorTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sensor_type = serializer.save()
        track_object_updated("Add", request.user, sensor_type, sensor_type.name, None)
        return Response(SensorTypeSerializer(sensor_type).data)


class SensorTypeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        sensor_type_id = kwargs.get("sensor_type_id")
        sensor_type = SensorType.objects.filter(id = sensor_type_id, deleted = False)[:1]
        if not sensor_type.count():
            raise Http404
        sensor_type = sensor_type[0]
        return Response(SensorTypeSerializer(sensor_type).data)

    def post(self, request, *args, **kwargs):
        sensor_type_id = kwargs.get("sensor_type_id")
        sensor_type = SensorType.objects.filter(id = sensor_type_id, deleted = False)[:1]
        if not sensor_type.count():
            raise Http404
        sensor_type = sensor_type[0]
        serializer = SensorTypeSerializer(sensor_type)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, sensor_type, sensor_type.name, request.data)
        serializer.update(sensor_type, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        sensor_type_id = kwargs.get("sensor_type_id")
        sensor_type = SensorType.objects.filter(id = sensor_type_id, deleted = False)[:1]
        if not sensor_type.count():
            raise Http404
        track_object_updated("Delete", request.user, sensor_type[0], sensor_type[0].name, None)
        sensor_type[0].delete()
        return Response("ok")
    
    
class FlowMeterTypesView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        return Response(FlowMeterTypeSerializer(FlowMeterType.objects.filter(deleted = False).order_by("name"), many = True).data)


class AddFlowMeterTypeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = FlowMeterTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        flow_meter_type = serializer.save()
        track_object_updated("Add", request.user, flow_meter_type, flow_meter_type.name, None)
        return Response(FlowMeterTypeSerializer(flow_meter_type).data)


class FlowMeterTypeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        flow_meter_type_id = kwargs.get("flow_meter_type_id")
        flow_meter_type = FlowMeterType.objects.filter(id = flow_meter_type_id, deleted = False)[:1]
        if not flow_meter_type.count():
            raise Http404
        flow_meter_type = flow_meter_type[0]
        return Response(FlowMeterTypeSerializer(flow_meter_type).data)

    def post(self, request, *args, **kwargs):
        flow_meter_type_id = kwargs.get("flow_meter_type_id")
        flow_meter_type = FlowMeterType.objects.filter(id = flow_meter_type_id, deleted = False)[:1]
        if not flow_meter_type.count():
            raise Http404
        flow_meter_type = flow_meter_type[0]
        serializer = FlowMeterTypeSerializer(flow_meter_type)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, flow_meter_type, flow_meter_type.name, request.data)
        serializer.update(flow_meter_type, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        flow_meter_type_id = kwargs.get("flow_meter_type_id")
        flow_meter_type = FlowMeterType.objects.filter(id = flow_meter_type_id, deleted = False)[:1]
        if not flow_meter_type.count():
            raise Http404
        track_object_updated("Delete", request.user, flow_meter_type[0], flow_meter_type[0].name, None)
        flow_meter_type[0].delete()
        return Response("ok")


class CompaniesListView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        return Response(CompanySerializer(Company.objects.filter(deleted = False).order_by("name"), many = True).data)
                        

class CreateCompanyView(APIView):
    permission_classes = (IsAuthenticated, SystemAdminPermission) 

    def post(self, request, *args, **kwargs):
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        track_object_updated("Add", request.user, company, company.name, request.data)
        return Response(CompanySerializer(company).data)
    
    
class CompanyView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company, read_access = True)
        return Response(CompanySerializer(company).data)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company)
        serializer = CompanySerializer(company)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, company, company.name, request.data)
        serializer.update(company, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)
        if not company.count():
            raise Http404
        check_company_permission(request.user, company[0])
        track_object_updated("Delete", request.user, company[0], company[0].name, None)
        company[0].delete()
        return Response("ok")
    

class CompanyLogoView(APIView):
    permission_classes = (IsAuthenticated, CompanyAdminPermission)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company)
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = None
            if request.user.is_authenticated:
                user = request.user
            track_object_updated("Edit", user, company, company.name, {"logo": str(form.cleaned_data['image'])})
            company.logo = form.cleaned_data['image']
            company.save()
            return HttpResponse('image upload success')
        else:
            print("form invalid")
            print(form.errors)
            return HttpResponse(str(form.errors))


class UserAvatarView(APIView):
    permission_classes = (IsAuthenticated, )

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        user = User.objects.filter(id = user_id, deleted = False)[:1]
        if not user.count():
            raise Http404
        user = user[0]
        check_user_permission(request.user, user)
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            request_user = None
            if request.user.is_authenticated:
                request_user = request.user
            track_object_updated("Edit", request_user, user, user.username, {"avatar": str(form.cleaned_data['image'])})
            user.avatar = form.cleaned_data['image']
            user.save()
            return HttpResponse('image upload success')
        else:
            print("form invalid")
            print(form.errors)
            return HttpResponse(str(form.errors))


class CompanyStaffView(APIView):
    permission_classes = (IsAuthenticated, )
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company, read_access = True)
        users = User.objects.filter(employer = company, deleted = False).order_by("last_name", "first_name")
        return Response(UserSerializer(users, many = True).data)


class CompanyAddStaffView(APIView):                             
    permission_classes = (IsAuthenticated, CompanyAdminPermission)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company)
        password = User.objects.make_random_password()
        if "password" in request.data:
            password = request.data["password"]
        else:
            request.data["password"] = password
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.employer = company
        user.save(update_fields = ["employer"])
        track_object_updated("Add", request.user, user, user.username)
        send_email(
            user.email,
            "email/account_created_subject.html",
            "email/account_created.html",
            user = user,
            password = password,
            use_html = True,
        )
        return Response(serializer.data)


class CompanyAddDepartmentView(APIView):                             
    permission_classes = (IsAuthenticated, CompanyAdminPermission)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company)
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        department.company = company
        department.save(update_fields = ["company"])
        track_object_updated("Add", request.user, department, department.name)
        return Response(serializer.data)
    

class CompanyDepartmentsView(APIView):
    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        departments = Department.objects.filter(company = company, deleted = False).order_by("name")
        return Response(DepartmentSerializer(departments, many = True).data)


class CompanyDepartmentView(APIView):
    permission_classes = (IsAuthenticated, )
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company, read_access = True)
        department_id = kwargs.get("department_id")
        department = Department.objects.filter(id = department_id, company = company, deleted = False)[:1]
        if not department.count():
            raise Http404
        department = department[0]
        return Response(DepartmentSerializer(department).data)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company)
        department_id = kwargs.get("department_id")
        department = Department.objects.filter(id = department_id, company = company, deleted = False)[:1]
        if not department.count():
            raise Http404
        department = department[0]
        serializer = DepartmentSerializer(department)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, department, department.name, request.data)
        serializer.update(department, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)
        if not company.count():
            raise Http404
        company = company[0]
        check_company_permission(request.user, company)
        department_id = kwargs.get("department_id")
        department = Department.objects.filter(id = department_id, company = company, deleted = False)
        if not department.count():
            raise Http404
        track_object_updated("Delete", request.user, department[0], department[0].name)
        department[0].delete()
        return Response("ok")


class DepartmentTypesView(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        return Response(DepartmentTypeSerializer(DepartmentType.objects.filter(deleted = False).order_by("name"), many = True).data)


class AddDepartmentTypeView(APIView):
    permission_classes = (IsAuthenticated, ) 

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = DepartmentTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department_type = serializer.save()
        track_object_updated("Add", request.user, department_type, department_type.name, None)
        return Response(DepartmentTypeSerializer(department_type).data)


class DepartmentTypeView(APIView):
    permission_classes = (IsAuthenticated, )
    
    def get(self, request, *args, **kwargs):
        type_id = kwargs.get("type_id")
        department_type = DepartmentType.objects.filter(id = type_id, deleted = False)[:1]
        if not department_type.count():
            raise Http404
        department_type = department_type[0]
        return Response(DepartmentTypeSerializer(department_type).data)

    def post(self, request, *args, **kwargs):
        type_id = kwargs.get("type_id")
        department_type = DepartmentType.objects.filter(id = type_id, deleted = False)[:1]
        if not department_type.count():
            raise Http404
        department_type = department_type[0]
        serializer = DepartmentTypeSerializer(department_type)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, department_type, department_type.name, request.data)
        serializer.update(department_type, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        type_id = kwargs.get("type_id")
        department_type = DepartmentType.objects.filter(id = type_id, deleted = False)[:1]
        if not department_type.count():
            raise Http404
        track_object_updated("Delete", request.user, department_type[0], department_type[0].name, None)
        department_type[0].delete()
        return Response("ok")

    
    
class CompanyAddObjectView(APIView):                             
    permission_classes = (IsAuthenticated, CompanyObjectAdminPermission)


    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_object_permission(request.user, company)
        serializer = CompanyObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_object = serializer.save()
        company_object.company = company
        company_object.save(update_fields = ["company"])
        track_object_updated("Add", request.user, company_object, company_object.name)
        if not settings.TESTING:
            address_coords = company_object.address_coords
            if address_coords and len(address_coords) == 2:
                req = requests.get("https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&lang=ru" % (address_coords[0], address_coords[1], settings.OPENWEATHERMAP_API_KEY))
                data = req.json()
                weather_data = CompanyObjectWeatherData(
                    company_object = company_object,
                    data = data,
                )
                weather_data.save()
                if "city" in data and "timezone" in data["city"]:
                    timezone = data["city"]["timezone"]
                    hours = timezone / 60 / 60
                    if hours >= 0:
                        company_object.timezone = "+%s" % hours
                    else:
                        company_object.timezone = "%s" % hours
                    company_object.save(update_fields = ["timezone"])
                serializer = CompanyObjectSerializer(company_object)
        return Response(serializer.data)
    

class AllCompanyObjectsView(APIView):
    permission_classes = (IsAuthenticated, CompanyObjectAdminPermission)
    
    def get(self, request, *args, **kwargs):
        limit = int(request.GET.get("limit", "10"))
        offset = int(request.GET.get("offset", "0"))
        objects = CompanyObject.objects.filter(deleted = False)
        permissions = request.user.get_permissions()
        if not permissions.status_admin_system:
            objects = objects.filter(company = request.user.employer)
        objects = objects.order_by("name")[offset:offset+limit]
        return Response(CompanyObjectSerializer(objects, many = True).data)
    
    
class CompanyObjectsView(APIView):
    permission_classes = (IsAuthenticated, CompanyObjectAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_object_permission(request.user, company, read_access = True)
        objects = CompanyObject.objects.filter(company = company, deleted = False).order_by("name")
        return Response(CompanyObjectSerializer(objects, many = True).data)


class CompanyObjectView(APIView):
    permission_classes = (IsAuthenticated, CompanyObjectAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_object_permission(request.user, company, read_access = True)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)[:1]
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        return Response(CompanyObjectSerializer(company_object).data)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_object_permission(request.user, company)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)[:1]
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        serializer = CompanyObjectSerializer(company_object)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, company_object, company_object.name, request.data)
        serializer.update(company_object, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id)
        if not company.count():
            raise Http404
        company = company[0]
        check_company_object_permission(request.user, company)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        track_object_updated("Delete", request.user, company_object[0], company_object[0].name)
        company_object[0].delete()
        return Response("ok")


class DevicesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_device_permission(request.user, company, read_access = True)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        devices = Device.objects.filter(company_object = company_object[0]).order_by("name")
        return Response(DeviceSerializer(devices, many = True).data)


class CompanyDevicesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        check_device_permission(request.user, company[0], read_access = True)
        devices = Device.objects.filter(company_object__company = company[0], deleted = False).order_by("name")
        return Response(DeviceSerializer(devices, many = True).data)


class DevicesListView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        user = request.user
        devices = None
        permissions = user.get_permissions()
        if permissions.status_admin_system:
            devices = Device.objects.filter(deleted = False).order_by("name")
        else:
            devices = Device.objects.filter(company_object__company = user.employer, deleted = False).order_by("name")
        return Response(DeviceSerializer(devices, many = True).data)


class CompanyModemsView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        check_modem_permission(request.user, company[0], read_access = True)
        devices = Modem.objects.filter(company_object__company = company[0], deleted = False).order_by("model")
        return Response(ModemSerializer(devices, many = True).data)


class ModemsListView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        user = request.user
        devices = None
        permissions = user.get_permissions()
        if permissions.status_admin_system:
            devices = Modem.objects.filter(deleted = False).order_by("model")
        else:
            devices = Modem.objects.filter(company_object__company = user.employer, deleted = False).order_by("model")
        return Response(ModemSerializer(devices, many = True).data)


class AddDeviceView(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_device_permission(request.user, company)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        device.company_object = company_object[0]
        device.save(update_fields = ["company_object"])
        track_object_updated("Add", request.user, device, device.__str__())
        return Response(serializer.data)


class DeviceView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company, read_access = True)
        return Response(DeviceSerializer(device).data)

    def post(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company)
        serializer = DeviceSerializer(device)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, device, device.__str__(), request.data)
        serializer.update(device, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company)
        track_object_updated("Delete", request.user, device, device.__str__())
        device.delete()
        return Response("ok")


class DeviceTimeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company, read_access = True)
        busy_devices = BusyDevice.objects.filter(device = device)[:1]
        if busy_devices.count():
            print("device %s is busy, waiting..." % device.id)
            time.sleep(settings.FRONTEND_DEVICE_WAIT_TIME)
            busy_devices = BusyDevice.objects.filter(device = device)[:1]
            if busy_devices.count():
                print("device %s is still busy, can't execute request..." % device.id)
                return HttpResponse(status = HTTP_503_SERVICE_UNAVAILABLE)
        busy_device = BusyDevice(device = device)
        busy_device.save()
        try:
            modem = device.modem
            log = ""
            connection_string = device.connection_string
            if not connection_string:
                connection_string = modem.connection_string
            log += '\nconnection_string: ' + connection_string
            connection_values = connection_string.split(":") 
            device_type = device.device_type
            device_obj = get_device_obj(device_type.model, connection_values[0], connection_values[1], device)
            log += "\nconnecting to device... "
            log += "\n" + device_obj.init_session()
            date = device_obj.get_current_time()
            device_obj.close_connection()
            log += "\ndevice time = %s " % date
            print(log)
            device.device_time = date.isoformat()
            device.save()
            device.set_status("ONLINE")
            return Response(DeviceSerializer(device).data)
        except Exception as ex:
            traceback.print_exc()
            device.set_status("OFFLINE")
            raise ex
        finally:
            busy_devices = BusyDevice.objects.filter(device = device)
            busy_devices.delete()
    
    
class SensorsView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company, read_access = True)
        sensors = Sensor.objects.filter(device = device, deleted = False).order_by("model")
        return Response(SensorSerializer(sensors, many = True).data)


class AddSensorView(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company)
        serializer = SensorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sensor = serializer.save()
        sensor.device = device
        sensor.save(update_fields = ["device"])
        track_object_updated("Add", request.user, sensor, sensor.model)
        return Response(serializer.data)

class SensorView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        sensor_id = kwargs.get("sensor_id")
        sensor = Sensor.objects.filter(id = sensor_id, deleted = False)[:1]
        if not sensor.count():
            raise Http404
        sensor = sensor[0]
        if sensor.device:
            device = sensor.device
            if device.company_object and device.company_object.company:
                check_device_permission(request.user, device.company_object.company, read_access = True)
        return Response(SensorSerializer(sensor).data)

    def post(self, request, *args, **kwargs):
        sensor_id = kwargs.get("sensor_id")
        sensor = Sensor.objects.filter(id = sensor_id, deleted = False)[:1]
        if not sensor.count():
            raise Http404
        sensor = sensor[0]
        if sensor.device:
            device = sensor.device
            if device.company_object and device.company_object.company:
                check_device_permission(request.user, device.company_object.company)
        serializer = SensorSerializer(sensor)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, sensor, sensor.model, request.data)
        serializer.update(sensor, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        sensor_id = kwargs.get("sensor_id")
        sensor = Sensor.objects.filter(id = sensor_id, deleted = False)[:1]
        if not sensor.count():
            raise Http404
        sensor = sensor[0]
        if sensor.device:
            device = sensor.device
            if device.company_object and device.company_object.company:
                check_device_permission(request.user, device.company_object.company)
        track_object_updated("Delete", request.user, sensor, sensor.model)
        sensor.delete()
        return Response("ok")
    
    
class FlowMetersView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company, read_access = True)
        flow_meters = FlowMeter.objects.filter(device = device, deleted = False).order_by("model")
        return Response(FlowMeterSerializer(flow_meters, many = True).data)


class AddFlowMeterView(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company)
        serializer = FlowMeterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        flow_meter = serializer.save()
        flow_meter.device = device
        flow_meter.save(update_fields = ["device"])
        track_object_updated("Add", request.user, flow_meter, flow_meter.model)
        return Response(serializer.data)

class FlowMeterView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        flow_meter_id = kwargs.get("flow_meter_id")
        flow_meter = FlowMeter.objects.filter(id = flow_meter_id, deleted = False)[:1]
        if not flow_meter.count():
            raise Http404
        flow_meter = flow_meter[0]
        if flow_meter.device:
            device = flow_meter.device
            if device.company_object and device.company_object.company:
                check_device_permission(request.user, device.company_object.company, read_access = True)
        return Response(FlowMeterSerializer(flow_meter).data)

    def post(self, request, *args, **kwargs):
        flow_meter_id = kwargs.get("flow_meter_id")
        flow_meter = FlowMeter.objects.filter(id = flow_meter_id, deleted = False)[:1]
        if not flow_meter.count():
            raise Http404
        flow_meter = flow_meter[0]
        if flow_meter.device:
            device = flow_meter.device
            if device.company_object and device.company_object.company:
                check_device_permission(request.user, device.company_object.company)
        serializer = FlowMeterSerializer(flow_meter)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, flow_meter, flow_meter.model, request.data)
        serializer.update(flow_meter, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        flow_meter_id = kwargs.get("flow_meter_id")
        flow_meter = FlowMeter.objects.filter(id = flow_meter_id, deleted = False)[:1]
        if not flow_meter.count():
            raise Http404
        flow_meter = flow_meter[0]
        if flow_meter.device:
            device = flow_meter.device
            if device.company_object and device.company_object.company:
                check_device_permission(request.user, device.company_object.company)
        track_object_updated("Delete", request.user, flow_meter, flow_meter.model)
        flow_meter.delete()
        return Response("ok")

    
    
class ModemsView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_modem_permission(request.user, device.company_object.company, read_access = True)
        modems = [device.modem]
        return Response(ModemSerializer(modems, many = True).data)


class AddModemView(APIView):                             
    permission_classes = (IsAuthenticated, ModemAdminPermission)

    def post(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_modem_permission(request.user, device.company_object.company)
        serializer = ModemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        modem = serializer.save()
        device.modem = modem
        device.save(update_fields = ["modem"])
        if device.company_object:
            modem.company_object = device.company_object
            modem.save(update_fields = ["company_object"])
        track_object_updated("Add", request.user, modem, modem.model)
        return Response(serializer.data)
    
    
class CompanyObjectAddModemView(APIView):                             
    permission_classes = (IsAuthenticated, ModemAdminPermission)

    def post(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_modem_permission(request.user, company)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        serializer = ModemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        modem = serializer.save()
        modem.company_object = company_object
        modem.save(update_fields = ["company_object"])
        track_object_updated("Add", request.user, modem, modem.model)
        return Response(serializer.data)


class CompanyObjectModemsView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_modem_permission(request.user, company, read_access = True)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        modems = Modem.objects.filter(company_object = company_object, deleted = False).order_by("model")
        return Response(ModemSerializer(modems, many = True).data)


class CompanyObjectMeteringPointsView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_device_permission(request.user, company, read_access = True)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        metering_points = MeteringPoint.objects.filter(company_object = company_object, deleted = False).order_by("name")
        return Response(MeteringPointSerializer(metering_points, many = True).data)


class CompanyObjectWeatherView(APIView):
    permission_classes = (IsAuthenticated, CompanyObjectAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_company_object_permission(request.user, company, read_access = True)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        date_from = request.GET.get("date_from", None)
        date_to = request.GET.get("date_to", None)
        if date_from:
            date_from = dateparse.parse_datetime(date_from)
        if date_to:
            date_to = dateparse.parse_datetime(date_to)
        weather_datas = CompanyObjectWeatherData.objects.filter(company_object = company_object)
        if date_from:
            weather_datas = weather_datas.filter(created__gte = date_from)            
        if date_to:
            weather_datas = weather_datas.filter(created__lt = date_to)            
        weather_datas = weather_datas.order_by("created")
        return Response(CompanyObjectWeatherDataSerializer(weather_datas, many = True).data)
    
    
class CompanyObjectDeviceDataView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        company_id = kwargs.get("company_id")
        company = Company.objects.filter(id = company_id, deleted = False)[:1]
        if not company.count():
            raise Http404
        company = company[0]
        check_device_permission(request.user, company, read_access = True)
        object_id = kwargs.get("object_id")
        company_object = CompanyObject.objects.filter(id = object_id, company = company, deleted = False)
        if not company_object.count():
            raise Http404
        company_object = company_object[0]
        result = {
            "object": company_object,
            "last_hour_datas": [],
        }
        #по каждой точке учета данного объекта получаем последний часовой отчет
        metering_points = MeteringPoint.objects.filter(deleted = False, company_object = company_object).order_by("id")
#         print(metering_points)
        for metering_point in metering_points:
            metering_point_datas = MeteringPointData.objects.filter(deleted = False, report_type = "HOURLY", metering_point = metering_point).order_by("-timestamp")[:1]
#             print(metering_point_datas)
            for data in metering_point_datas:
                result["last_hour_datas"].append(data)
        return Response(CompanyObjectDeviceDataSerializer(result).data)



class DeviceModemView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_modem_permission(request.user, device.company_object.company, read_access = True)
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        return Response(ModemSerializer(modem).data)

    def post(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_modem_permission(request.user, device.company_object.company)
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        serializer = ModemSerializer(modem)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, modem, modem.model, request.data)
        serializer.update(modem, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_modem_permission(request.user, device.company_object.company)
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        track_object_updated("Delete", request.user, modem, modem.model)
        modem.delete()
        return Response("ok")
    
    
class ModemView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        if modem.company_object and modem.company_object.company:
            check_modem_permission(request.user, modem.company_object.company, read_access = True)
        return Response(ModemSerializer(modem).data)

    def post(self, request, *args, **kwargs):
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        if modem.company_object and modem.company_object.company:
            check_modem_permission(request.user, modem.company_object.company)
        serializer = ModemSerializer(modem)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, modem, modem.model, request.data)
        serializer.update(modem, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        if modem.company_object and modem.company_object.company:
            check_modem_permission(request.user, modem.company_object.company)
        track_object_updated("Delete", request.user, modem, modem.model)
        modem.delete()
        return Response("ok")
    
    
class TasksView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company, read_access = True)
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, device = device, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        tasks = Task.objects.filter(metering_point__modem = modem, deleted = False).order_by("name")
        return Response(TaskSerializer(tasks, many = True).data)
    
    
class ModemTasksView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        if modem.company_object and modem.company_object.company:
            check_modem_permission(request.user, modem.company_object.company, read_access = True)
        tasks = Task.objects.filter(metering_point__modem = modem, deleted = False).order_by("name")
        return Response(TaskSerializer(tasks, many = True).data)


class ModemQueriesView(APIView):
    permission_classes = (IsAuthenticated, ModemAdminPermission)
    
    def get(self, request, *args, **kwargs):
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        if modem.company_object and modem.company_object.company:
            check_modem_permission(request.user, modem.company_object.company, read_access = True)
        queries = Query.objects.filter(task__metering_point__modem = modem, deleted = False).order_by("name")
        return Response(QuerySerializer(queries, many = True).data)


class MeteringPointQueriesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        queries = Query.objects.filter(task__metering_point = metering_point, deleted = False).order_by("name")
        return Response(QuerySerializer(queries, many = True).data)


class MeteringPointAddTaskView(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        task.metering_point = metering_point
        task.save(update_fields = ["metering_point"])
        track_object_updated("Add", request.user, task, task.name)
        return Response(serializer.data)
    
    
class MeteringPointTasksView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        tasks = Task.objects.filter(metering_point = metering_point, deleted = False).order_by("name")
        return Response(TaskSerializer(tasks, many = True).data)


class TaskView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        task_id = kwargs.get("task_id")
        task = Task.objects.filter(id = task_id, deleted = False)[:1]
        if not task.count():
            raise Http404
        task = task[0]
        if task.metering_point:
            metering_point = task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        return Response(TaskSerializer(task).data)

    def post(self, request, *args, **kwargs):
        task_id = kwargs.get("task_id")
        task = Task.objects.filter(id = task_id, deleted = False)[:1]
        if not task.count():
            raise Http404
        task = task[0]
        if task.metering_point:
            metering_point = task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company)
        serializer = TaskSerializer(task)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, task, task.name, request.data)
        serializer.update(task, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        task_id = kwargs.get("task_id")
        task = Task.objects.filter(id = task_id, deleted = False)[:1]
        if not task.count():
            raise Http404
        task = task[0]
        if task.metering_point:
            metering_point = task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company)
        track_object_updated("Delete", request.user, task, task.name)
        task.delete()
        return Response("ok")
    
    
class QueriesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        task_id = kwargs.get("task_id")
        task = Task.objects.filter(id = task_id, deleted = False)[:1]
        if not task.count():
            raise Http404
        task = task[0]
        if task.metering_point:
            metering_point = task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        queries = Query.objects.filter(task = task, deleted = False).order_by("name")
        return Response(QuerySerializer(queries, many = True).data)


class AddQueryView(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        task_id = kwargs.get("task_id")
        task = Task.objects.filter(id = task_id, deleted = False)[:1]
        if not task.count():
            raise Http404
        task = task[0]
        if task.metering_point:
            metering_point = task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company)
        serializer = QuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.save()
        query.task = task
        query.save(update_fields = ["task"])
        track_object_updated("Add", request.user, query, query.name)
        return Response(serializer.data)


class QueryView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        query_id = kwargs.get("query_id")
        query = Query.objects.filter(id = query_id, deleted = False)[:1]
        if not query.count():
            raise Http404
        query = query[0]
        if query.task and query.task.metering_point:
            metering_point = query.task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        return Response(QuerySerializer(query).data)

    def post(self, request, *args, **kwargs):
        query_id = kwargs.get("query_id")
        query = Query.objects.filter(id = query_id, deleted = False)[:1]
        if not query.count():
            raise Http404
        query = query[0]
        if query.task and query.task.metering_point:
            metering_point = query.task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company)
        serializer = QuerySerializer(query)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, query, query.name, request.data)
        serializer.update(query, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        query_id = kwargs.get("query_id")
        query = Query.objects.filter(id = query_id, deleted = False)[:1]
        if not query.count():
            raise Http404
        query = query[0]
        if query.task and query.task.metering_point:
            metering_point = query.task.metering_point
            if metering_point.company_object and metering_point.company_object.company:
                check_device_permission(request.user, metering_point.company_object.company)
        track_object_updated("Delete", request.user, query, query.name)
        query.delete()
        return Response("ok")


class ModemDevicesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        modem_id = kwargs.get("modem_id")
        modem = Modem.objects.filter(id = modem_id, deleted = False)[:1]
        if not modem.count():
            raise Http404
        modem = modem[0]
        if modem.company_object and modem.company_object.company:
            check_device_permission(request.user, modem.company_object.company, read_access = True)
        devices = Device.objects.filter(modem = modem, deleted = False).order_by("name")
        return Response(DeviceSerializer(devices, many = True).data)


class TotalsView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        data = dict()
        user = request.user
        permissions = user.get_permissions()
        if permissions and permissions.status_admin_system:
            data["companies"] = Company.objects.filter(deleted = False).count()
            data["users"] = User.objects.filter(employer__isnull = False, deleted = False).count()
            data["company_objects"] = CompanyObject.objects.filter(deleted = False).count()
            total_modems = Modem.objects.filter(deleted = False).count()
            active_modems = Modem.objects.filter(active = True, deleted = False).count()
            inactive_modems = total_modems - active_modems
            data["modems"] = total_modems
            data["active_modems"] = active_modems
            data["inactive_modems"] = inactive_modems
            data["devices"] = Device.objects.filter(deleted = False).count()
        else:
            data["companies"] = 1
            data["users"] = User.objects.filter(employer = user.employer, deleted = False).count()
            data["company_objects"] = CompanyObject.objects.filter(company = user.employer, deleted = False).count()
            total_modems = Modem.objects.filter(company_object__company = user.employer, deleted = False).count()
            active_modems = Modem.objects.filter(company_object__company = user.employer, active = True, deleted = False).count()
            inactive_modems = total_modems - active_modems
            data["modems"] = total_modems
            data["active_modems"] = active_modems
            data["inactive_modems"] = inactive_modems
            data["devices"] = Device.objects.filter(company_object__company = user.employer, deleted = False).count()
        return Response(TotalsSerializer(data).data)


class MeteringPoints(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company, read_access = True)
        metering_points = MeteringPoint.objects.filter(device = device, deleted = False).order_by("name")
        return Response(MeteringPointSerializer(metering_points, many = True).data)


class AddMeteringPoint(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        device_id = kwargs.get("device_id")
        device = Device.objects.filter(id = device_id, deleted = False)[:1]
        if not device.count():
            raise Http404
        device = device[0]
        if device.company_object and device.company_object.company:
            check_device_permission(request.user, device.company_object.company)
        serializer = MeteringPointSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        metering_point = serializer.save()
        metering_point.device = device
        if device.company_object:
            metering_point.company_object = device.company_object
        if device.modem:
            metering_point.modem = device.modem
        metering_point.save()
        track_object_updated("Add", request.user, metering_point, metering_point.name)
        return Response(serializer.data)


class MeteringPointView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        return Response(MeteringPointSerializer(metering_point).data)

    def post(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        serializer = MeteringPointSerializer(metering_point)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, metering_point, metering_point.name, request.data)
        serializer.update(metering_point, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        track_object_updated("Delete", request.user, metering_point, metering_point.name)
        metering_point.delete()
        return Response("ok")
    
    
class MeteringPointsDataList(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        datas = MeteringPointData.objects.filter(metering_point = metering_point, deleted = False, report_type = "DAILY").order_by("id")
        return Response(MeteringPointDataSerializer(datas, many = True).data)


class MeteringPointsDataListByReportType(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        report_type = kwargs.get("report_type")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        datas = MeteringPointData.objects.filter(metering_point = metering_point, deleted = False, report_type = report_type).order_by("id")
        return Response(MeteringPointDataSerializer(datas, many = True).data)


class RequestMeteringPointData(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        modem = metering_point.modem
        device = metering_point.device
        busy_devices = BusyDevice.objects.filter(device = device)[:1]
        if busy_devices.count():
            print("device %s is busy, waiting..." % device.id)
            time.sleep(settings.FRONTEND_DEVICE_WAIT_TIME)
            busy_devices = BusyDevice.objects.filter(device = device)[:1]
            if busy_devices.count():
                print("device %s is still busy, can't execute request..." % device.id)
                return HttpResponse(status = HTTP_503_SERVICE_UNAVAILABLE)
        busy_device = BusyDevice(device = device)
        busy_device.save()
        try:
            log = ""
            connection_string = modem.connection_string
            log += '\nconnection_string: ' + connection_string
            connection_values = connection_string.split(":") 
            device_type = metering_point.device.device_type
            device_obj = get_device_obj(device_type.model, connection_values[0], connection_values[1], device)
            log += "\nconnecting to device... "
            log += "\n" + device_obj.init_session()
            date = device_obj.get_current_time()
            log += "\ndevice time = %s " % date
            log += "\nrequesting data... "
            try:
                input_number = int(metering_point.input_number)
            except Exception as ex:
                input_number = 1
            raw_data, data, request_log, all_data = device_obj.request_data("DAILY", input_number, metering_point.device.device_type.parameters)
            device_obj.close_connection()
            log += request_log
    #         print("got data:", data)
            #TODO parse data
            metering_point_data = MeteringPointData(
                metering_point = metering_point,
                device_type = device.device_type,
                timestamp = date,
                #FIXME replace data
                data = data,
                raw_data = raw_data,
                log = log,
                all_data = all_data,
            )
            metering_point_data.save()
            metering_point_data.calculate_data()
            track_object_updated("Add", request.user, metering_point_data, metering_point_data.__str__())
            device.set_status("ONLINE")
            return Response(MeteringPointSerializer(metering_point).data)
        except Exception as ex:
            traceback.print_exc()
            device.set_status("OFFLINE")
            raise ex
        finally:
            busy_devices = BusyDevice.objects.filter(device = device)
            busy_devices.delete()


class RequestMeteringPointDataByReportType(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        report_type = kwargs.get("report_type")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        modem = metering_point.modem
        device = metering_point.device
        busy_devices = BusyDevice.objects.filter(device = device)[:1]
        if busy_devices.count():
            print("device %s is busy, waiting..." % device.id)
            time.sleep(settings.FRONTEND_DEVICE_WAIT_TIME)
            busy_devices = BusyDevice.objects.filter(device = device)[:1]
            if busy_devices.count():
                print("device %s is still busy, can't execute request..." % device.id)
                return HttpResponse(status = HTTP_503_SERVICE_UNAVAILABLE)
        busy_device = BusyDevice(device = device)
        busy_device.save()
        try:
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
            #TODO parse data
            metering_point_data = MeteringPointData(
                metering_point = metering_point,
                device_type = device.device_type,
                timestamp = date,
                #FIXME replace data
                data = data,
                raw_data = raw_data,
                log = log,
                report_type = report_type,
                all_data = all_data,
            )
            metering_point_data.save()
            metering_point_data.calculate_data()
            track_object_updated("Add", request.user, metering_point_data, metering_point_data.__str__())
            device.set_status("ONLINE")
            return Response(MeteringPointSerializer(metering_point).data)
        except Exception as ex:
            traceback.print_exc()
            device.set_status("OFFLINE")
            raise ex
        finally:
            busy_devices = BusyDevice.objects.filter(device = device)
            busy_devices.delete()


class AddMeteringPointData(APIView):                             
    permission_classes = (IsAuthenticated, DeviceAdminPermission)

    def post(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        serializer = MeteringPointDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        metering_point_data = serializer.save()
        metering_point_data.metering_point = metering_point
        metering_point_data.save()
        track_object_updated("Add", request.user, metering_point_data, metering_point_data.__str__())
        return Response(serializer.data)


class MeteringPointDataView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company, read_access = True)
        data_id = kwargs.get("data_id")
        metering_point_data = MeteringPointData.objects.filter(metering_point = metering_point, id = data_id, deleted = False)[:1]
        if not metering_point_data.count():
            raise Http404
        metering_point_data = metering_point_data[0]
        return Response(MeteringPointDataSerializer(metering_point_data).data)

    def post(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        data_id = kwargs.get("data_id")
        metering_point_data = MeteringPointData.objects.filter(metering_point = metering_point, id = data_id, deleted = False)[:1]
        if not metering_point_data.count():
            raise Http404
        metering_point_data = metering_point_data[0]
        serializer = MeteringPointDataSerializer(metering_point_data)
        serializer.run_validation(request.data)
        track_object_updated("Add", request.user, metering_point_data, metering_point_data.__str__(), request.data)
        serializer.update(metering_point_data, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        metering_point_id = kwargs.get("point_id")
        metering_point = MeteringPoint.objects.filter(id = metering_point_id, deleted = False)[:1]
        if not metering_point.count():
            raise Http404
        metering_point = metering_point[0]
        if metering_point.company_object and metering_point.company_object.company:
            check_device_permission(request.user, metering_point.company_object.company)
        data_id = kwargs.get("data_id")
        metering_point_data = MeteringPointData.objects.filter(metering_point = metering_point, id = data_id, deleted = False)[:1]
        if not metering_point_data.count():
            raise Http404
        metering_point_data = metering_point_data[0]
        track_object_updated("Delete", request.user, metering_point_data, metering_point_data.__str__())
        metering_point_data.delete()
        return Response("ok")


class UserRolesView(APIView):
    SYSTEM_ADMIN_ROLES = [
        "Админ системы",
        "Админ компании",
        "Менеджер объектов",
        "Менеджер модемов",
        "Менеджер приборов учета",
    ]

    COMPANY_ADMIN_ROLES = [
        "Админ компании",
        "Менеджер объектов",
        "Менеджер модемов",
        "Менеджер приборов учета",
    ]

    COMPANY_OBJECT_ADMIN_ROLES = [
        "Менеджер объектов",
        "Менеджер модемов",
        "Менеджер приборов учета",
    ]

    MODEM_ADMIN_ROLES = [
        "Менеджер модемов",
        "Менеджер приборов учета",
    ]

    DEVICE_ADMIN_ROLES = [
        "Менеджер приборов учета",
    ]
    
    def check_roles_exist(self):
        for role in self.SYSTEM_ADMIN_ROLES:
            permissions = UserPermissions.objects.filter(role = role)[:1]
            if not permissions.count():
                permissions = UserPermissions(role = role)
                if role == "Админ системы":
                    permissions.status_admin_system = True
                elif role == "Админ компании":
                    permissions.status_admin_company = True
                elif role == "Менеджер объектов":
                    permissions.status_admin_company_object = True
                elif role == "Менеджер модемов":
                    permissions.status_admin_modem = True
                elif role == "Менеджер приборов учета":
                    permissions.status_admin_device = True
                permissions.save()
#         print("have %s permissions" % UserPermissions.objects.all().count())
        
    def get_permissions_list(self, roles):
        permissions_list = []
        for role in roles:
            permissions = UserPermissions.objects.filter(role = role)[:1]
            if permissions.count():
                permissions_list.append(permissions[0])
        return permissions_list
    
    def get(self, request, *args, **kwargs):
        self.check_roles_exist()    #FIXME: remove in the future
        if request.user and request.user.is_authenticated:
            permissions = request.user.get_permissions()
            if not permissions:
                #FIXME change permissions for anonymous user
                return Response(UserPermissionsSerializer(self.get_permissions_list(self.COMPANY_ADMIN_ROLES), many = True).data)
            if permissions.status_admin_system:
                return Response(UserPermissionsSerializer(self.get_permissions_list(self.SYSTEM_ADMIN_ROLES), many = True).data)
            if permissions.status_admin_company:
                return Response(UserPermissionsSerializer(self.get_permissions_list(self.COMPANY_ADMIN_ROLES), many = True).data)
            if permissions.status_admin_company_object:
                return Response(UserPermissionsSerializer(self.get_permissions_list(self.COMPANY_OBJECT_ADMIN_ROLES), many = True).data)
            if permissions.status_admin_company_object:
                return Response(UserPermissionsSerializer(self.get_permissions_list(self.MODEM_ADMIN_ROLES), many = True).data)
            return Response(UserPermissionsSerializer(self.get_permissions_list(self.DEVICE_ADMIN_ROLES), many = True).data)
        else:
            #FIXME change permissions for anonymous user
            return Response(UserPermissionsSerializer(self.get_permissions_list(self.COMPANY_ADMIN_ROLES), many = True).data)
                    
                    
class SuggestionsFiasView(APIView):                  
    permission_classes = (IsAuthenticated, )
    
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code", "")
        req = requests.post(
            url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/address",
            headers = {
                "Authorization": "Token %s" % settings.DATATA_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json = {
                "query": code,
            }
        )
        data = req.json()
        result = []
        for data_record in data["suggestions"]:
            record = {
                "address": data_record["unrestricted_value"],
                "address_coords": [
                    data_record["data"]["geo_lat"],
                    data_record["data"]["geo_lon"],
                ]
            }
            result.append(record)
        return Response(FiasDataSerializer(result, many = True).data)


class SuggestionsAddressView(APIView):                  
    permission_classes = (IsAuthenticated, )
    
    def get(self, request, *args, **kwargs):
        address = request.GET.get("address", "")
        req = requests.post(
            url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address",
            headers = {
                "Authorization": "Token %s" % settings.DATATA_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json = {
                "query": address,
            }
        )
        data = req.json()
        result = []
        for data_record in data["suggestions"]:
            record = {
                "address": data_record["unrestricted_value"],
                "fias_code": data_record["data"]["fias_id"],
                "timezone": data_record["data"]["timezone"],
                "address_coords": [
                    data_record["data"]["geo_lat"],
                    data_record["data"]["geo_lon"],
                ]
            }
            result.append(record)
        return Response(AddressSuggestionDataSerializer(result, many = True).data)
    
    
    
class HeatSupplySchemesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def get(self, request):
        user = request.user
        permissions = user.get_permissions()
        if not permissions:
            raise HttpResponseForbidden("unsufficient permissions")
        if permissions.status_admin_system:
            return Response(HeatSupplySchemeSerializer(HeatSupplyScheme.objects.filter(deleted = False).order_by("name"), many = True).data)
        return Response(HeatSupplySchemeSerializer(HeatSupplyScheme.objects.filter(deleted = False, user__employer = user.employer).order_by("name"), many = True).data)

class AddHeatSupplySchemeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = HeatSupplySchemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        track_object_updated("Add", request.user, obj, obj.name, None)
        return Response(HeatSupplySchemeSerializer(obj).data)


class HeatSupplySchemeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer, read_access = True)
        return Response(HeatSupplySchemeSerializer(obj).data)

    def post(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer)
        serializer = HeatSupplySchemeSerializer(obj)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, obj, obj.name, request.data)
        serializer.update(obj, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        if obj[0].user and obj[0].user.employer:
            check_device_permission(request.user, obj.user.employer)
        track_object_updated("Delete", request.user, obj[0], obj[0].name, None)
        obj[0].delete()
        return Response("ok")
    
    
class MeteringPointHeatSupplySchemesView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def get(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer, read_access = True)
        return Response(MeteringPointHeatSupplySchemeSerializer(MeteringPointHeatSupplyScheme.objects.filter(heat_supply_scheme = obj, deleted = False).order_by("id"), many = True).data)


class AddMeteringPointHeatSupplySchemeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission) 

    def post(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer)
        serializer = MeteringPointHeatSupplySchemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mp_obj = serializer.save()
        mp_obj.heat_supply_scheme = obj
        mp_obj.save()
        track_object_updated("Add", request.user, mp_obj, mp_obj.__str__(), None)
        return Response(MeteringPointHeatSupplySchemeSerializer(mp_obj).data)


class MeteringPointHeatSupplySchemeView(APIView):
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer, read_access = True)
        param_id = kwargs.get("param_id")
        mp_obj = MeteringPointHeatSupplyScheme.objects.filter(heat_supply_scheme = obj, id = param_id, deleted = False)
        if not mp_obj.count():
            raise Http404
        mp_obj = mp_obj[0]
        return Response(MeteringPointHeatSupplySchemeSerializer(mp_obj).data)

    def post(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer)
        param_id = kwargs.get("param_id")
        mp_obj = MeteringPointHeatSupplyScheme.objects.filter(heat_supply_scheme = obj, id = param_id, deleted = False)
        if not mp_obj.count():
            raise Http404
        mp_obj = mp_obj[0]
        serializer = MeteringPointHeatSupplySchemeSerializer(mp_obj)
        serializer.run_validation(request.data)
        track_object_updated("Edit", request.user, mp_obj, mp_obj.__str__(), request.data)
        serializer.update(mp_obj, request.data)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        id = kwargs.get("id")
        obj = HeatSupplyScheme.objects.filter(id = id, deleted = False)[:1]
        if not obj.count():
            raise Http404
        obj = obj[0]
        if obj.user and obj.user.employer:
            check_device_permission(request.user, obj.user.employer)
        param_id = kwargs.get("param_id")
        mp_obj = MeteringPointHeatSupplyScheme.objects.filter(heat_supply_scheme = obj, id = param_id, deleted = False)
        if not mp_obj.count():
            raise Http404
        mp_obj = mp_obj[0]
        track_object_updated("Delete", request.user, mp_obj, mp_obj.__str__(), None)
        mp_obj.delete()
        return Response("ok")


class SearchView(APIView):                  
    permission_classes = (IsAuthenticated, )
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get("query", "")
        filter = request.GET.get("filter", "all")
        date_from = request.GET.get("date_from", None)
        date_to = request.GET.get("date_to", None)
        if date_from:
            date_from = dateparse.parse_datetime(date_from)
        if date_to:
            date_to = dateparse.parse_datetime(date_to)
        users = []
        companies = []
        company_objects = []
        metering_points = []
        modems = []
        devices = []
        user = request.user
        permissions = request.user.get_permissions()
        if filter == "all":
            search_results = watson.search(query)
#             print(search_results)
            for search_result in search_results:
                obj = search_result.object
                if obj.deleted:
                    continue
                meta = obj._meta
                model_name = meta.object_name
                if model_name == "User":
                    if date_from and obj.date_joined < date_from:
                        continue
                    if date_to and obj.date_joined >= date_to:
                        continue
                elif not model_name == "DeviceType":
                    if date_from and obj.created < date_from:
                        continue
                    if date_to and obj.created >= date_to:
                        continue
                if model_name == "User":
                    if permissions.status_admin_system:
                        users.append(obj)
                    elif permissions.status_admin_company:
                        if obj.employer == user.employer:
                            users.append(obj)
                    else:
                        if obj.id == user.id:
                            users.append(obj)                        
                elif model_name == "Company":
                    if permissions.status_admin_system:
                        companies.append(obj)
                    elif permissions.status_admin_company:
                        if obj == user.employer:
                            companies.append(obj)
                elif model_name == "CompanyObject":
                    if permissions.status_admin_system:
                        company_objects.append(obj)
                    elif permissions.status_admin_company or permissions.status_admin_company_object:
                        if obj.company == user.employer:
                            company_objects.append(obj)
                elif model_name == "MeteringPoint":
                    if permissions.status_admin_system:
                        metering_points.append(obj)
                    elif permissions.status_admin_company or permissions.status_admin_device:
                        if obj.company_object.company == user.employer:
                            metering_points.append(obj)
                elif model_name == "Modem":
                    if permissions.status_admin_system:
                        modems.append(obj)
                    elif permissions.status_admin_company or permissions.status_admin_modem:
                        if obj.company_object.company == user.employer:
                            modems.append(obj)
                elif model_name == "DeviceType":
                    devs = Device.objects.filter(device_type = obj)
                    if date_from:
                        devs = devs.filter(created__gte = date_from)
                    if date_to:
                        devs = devs.filter(created__lt = date_to)
                    devs = devs.order_by("name")
                    for device in devs:
                        if permissions.status_admin_system:
                            devices.append(device)
                        elif permissions.status_admin_company or permissions.status_admin_device:
                            if device.company_object.company == user.employer:
                                devices.append(device)
                elif model_name == "Device":
                    if permissions.status_admin_system:
                        devices.append(obj)
                    elif permissions.status_admin_company or permissions.status_admin_device:
                        if obj.company_object.company == user.employer:
                            devices.append(obj)
                elif model_name == "Device":
                    if permissions.status_admin_system:
                        devices.append(obj)
                    elif permissions.status_admin_company or permissions.status_admin_device:
                        if obj.company_object.company == user.employer:
                            devices.append(obj)
        elif filter == "users":
            search_results = watson.filter(User, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                if date_from and obj.date_joined < date_from:
                    continue
                if date_to and obj.date_joined >= date_to:
                    continue
                if permissions.status_admin_system:
                    users.append(obj)
                elif permissions.status_admin_company:
                    if obj.employer == user.employer:
                        users.append(obj)
                else:
                    if obj.id == user.id:
                        users.append(obj)
        elif filter == "companies":
            search_results = watson.filter(Company, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                if date_from and obj.created < date_from:
                    continue
                if date_to and obj.created >= date_to:
                    continue
                if permissions.status_admin_system:
                    companies.append(obj)
                elif permissions.status_admin_company:
                    if obj == user.employer:
                        companies.append(obj)
        elif filter == "company_objects":
            search_results = watson.filter(CompanyObject, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                if date_from and obj.created < date_from:
                    continue
                if date_to and obj.created >= date_to:
                    continue
                if permissions.status_admin_system:
                    company_objects.append(obj)
                elif permissions.status_admin_company or permissions.status_admin_company_object:
                    if obj.company == user.employer:
                        company_objects.append(obj)
        elif filter == "metering_points":
            search_results = watson.filter(MeteringPoint, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                if date_from and obj.created < date_from:
                    continue
                if date_to and obj.created >= date_to:
                    continue
                if permissions.status_admin_system:
                    metering_points.append(obj)
                elif permissions.status_admin_company or permissions.status_admin_device:
                    if obj.company_object.company == user.employer:
                        metering_points.append(obj)
        elif filter == "modems":
            search_results = watson.filter(Modem, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                if date_from and obj.created < date_from:
                    continue
                if date_to and obj.created >= date_to:
                    continue
                if permissions.status_admin_system:
                    modems.append(obj)
                elif permissions.status_admin_company or permissions.status_admin_modem:
                    if obj.company_object.company == user.employer:
                        modems.append(obj)
        elif filter == "devices":
            search_results = watson.filter(DeviceType, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                devs = Device.objects.filter(device_type = obj)
                if date_from:
                    devs = devs.filter(created__gte = date_from)
                if date_to:
                    devs = devs.filter(created__lt = date_to)
                devs = devs.order_by("name")
                for device in devs:
                    if permissions.status_admin_system:
                        devices.append(device)
                    elif permissions.status_admin_company or permissions.status_admin_device:
                        if device.company_object.company == user.employer:
                            devices.append(device)
            search_results = watson.filter(Device, query)
            for obj in search_results:
                if obj.deleted:
                    continue
                if date_from and obj.created < date_from:
                    continue
                if date_to and obj.created >= date_to:
                    continue
                if permissions.status_admin_system:
                    devices.append(obj)
                elif permissions.status_admin_company or permissions.status_admin_device:
                    if obj.company_object.company == user.employer:
                        devices.append(obj)
        result = {
            "users": users,
            "companies": companies,
            "company_objects": company_objects,
            "metering_points": metering_points,
            "modems": modems,
            "devices": devices,
        }
        return Response(SearchResultSerializer(result).data)


class ReportView(APIView):                  
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def get(self, request, *args, **kwargs):
        result = generate_report(request)
        return Response(ReportSerializer(result).data)


class ReportDownloadView(APIView):                  
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def process_request(self, request, *args, **kwargs):
        file_type = kwargs.get("file_type")
        headers = request.GET.get("columns", None)
        result = None
        if file_type == "CSV":
            result = generate_report(request)
        if file_type == "PDF":
            data, device_type = generate_separate_objects_report(request)
            return create_pdf_report(
                request, 
                data, 
                device_type.get_template_file_name(file_type), 
                headers = headers
            )
        elif file_type == "DOCX":
            data, device_type = generate_separate_objects_report(request)
            template_file_name = "%s/templates/%s" % (settings.BASE_DIR, device_type.get_template_file_name(file_type))
            dir = "%s/reports" % settings.MEDIA_ROOT
            Path(dir).mkdir(parents=True, exist_ok=True)
            # Store the dataframe in Excel file
            filename = "%s/report-%s.docx" % (dir, randint(0, 100000))
            create_docx_report(data, template_file_name, filename, headers = headers)
            mimetypes.init()
            extension = ".docx"
            extension = extension.lower()
            content_type = ""
            if extension in mimetypes.types_map:
                content_type = mimetypes.types_map[extension]
            with open(filename, 'rb') as f:
                file_data = f.read()
            response = HttpResponse(file_data, content_type=content_type)
            title = "report.docx"
            if not title.lower().endswith(extension.lower()):
                title = "%s%s" % (title, extension)
            response['Content-Disposition'] = 'attachment; filename="%s"' % requests.utils.quote(title)
            return response
        elif file_type == "XLS":
            result = generate_report(request, for_excel=True)
            context = result
            if headers:
                context['headers'] = headers.split(',')

            dir = "%s/reports" % settings.MEDIA_ROOT
            Path(dir).mkdir(parents=True, exist_ok=True)
            filename = "%s/report-%s.xlsx" % (dir, randint(0, 100000))
            create_excel_report(context, filename)

            # template = loader.get_template("report.html")
            # html = template.render(context)
            # import pandas as pd
            # table = pd.read_html(html)[0]
            # table.to_excel(filename)

            mimetypes.init()
            extension = ".xlsx"
            extension = extension.lower()
            content_type = ""
            if extension in mimetypes.types_map:
                content_type = mimetypes.types_map[extension]
            with open(filename, 'rb') as f:
                file_data = f.read()
            response = HttpResponse(file_data, content_type=content_type)
            title = "report.xls"
            if not title.lower().endswith(extension.lower()):
                title = "%s%s" % (title, extension)
            response['Content-Disposition'] = 'attachment; filename="%s"' % requests.utils.quote(title)
            return response
        elif file_type == "CSV":
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="report.csv"'
            writer = csv.writer(response)
            writer.writerow(result["headers"])
            for row in result["values"]:
                writer.writerow(row.data)
            return response
        return TemplateResponse(request, "report.html", result)
    
    def get(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)

    def head(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)
    
class ReportEmailView(APIView):                  
    permission_classes = (IsAuthenticated, DeviceAdminPermission)
    
    def process_request(self, request, *args, **kwargs):
        file_type = kwargs.get("file_type")
        username = request.GET.get("username", "") 
        headers = request.GET.get("columns", None)
        users = User.objects.filter(username = username)[:1]
        emails = request.GET.get("emails", None)
        if not emails:
            emails = username
        if not users.count() and not emails:
            raise Http404
        user = users[0] if users.count() else None
        periodic_task = request.GET.get("periodic_task", "false")
        objects = request.GET.get("objects", "")
        report_type = request.GET.get("report_type", "DAILY")
        if not periodic_task == "false":
            date_from = request.GET.get("date_from", None)
            date_to = request.GET.get("date_to", None)
            if date_from:
                date_from = dateparse.parse_datetime(date_from)
            if date_to:
                date_to = dateparse.parse_datetime(date_to)
            object_ids = None
            if objects:
                object_ids = json.loads("[%s]" % objects)
        #         print("object_ids = " , object_ids)
            permissions = request.user.get_permissions()
            company_objects = CompanyObject.objects.filter(deleted = False)
            if not permissions.status_admin_system and user:
                company_objects = company_objects.filter(company = user.employer)
            if object_ids:
                company_objects = company_objects.filter(id__in = object_ids)
            send_type = request.GET.get("send_type", "DAILY")
            time = request.GET.get("time", None)
            if time:
                time = dateparse.parse_datetime(time)
            report_task = ReportTask(
                user = user,
                request_user = request.user,
                time = time,
                date_from = date_from,
                date_to = date_to,
                report_type = report_type,
                send_type = send_type,
                file_type = file_type,
                emails = emails,
                headers = headers,
            )
            report_task.save()
            for company_object in company_objects:
                report_task.company_objects.add(company_object)
            track_object_updated("Add", request.user, report_task, "report task for user %s" % user)
        if check_mock_reports(objects, file_type, emails, report_type):
            return HttpResponse("ok")

        result = None
        if file_type == "CSV":
            result = generate_report(request, report_user = user)
        if file_type == "PDF":
            data, device_type = generate_separate_objects_report(request, report_user = user)
            if emails:
                emails_list = emails.split(",")
                for email in emails_list:
                    email_users = User.objects.filter(email = email)
                    if email_users.count():
                        email_user = email_users[0]
                        data, device_type = generate_separate_objects_report(request, report_user = email_user)
                    response = create_pdf_report(
                        request, 
                        data, 
                        device_type.get_template_file_name(file_type), 
                        headers = headers
                    )
                    msg = EmailMessage(
                        subject = "report",
                        body = '',
                        from_email = settings.DEFAULT_FROM_EMAIL,
                        to = [email],
                    )            
                    msg.attach('report.pdf', response.rendered_content, 'application/pdf')
                    msg.send()    
            elif user:
                response = create_pdf_report(
                    request, 
                    data, 
                    device_type.get_template_file_name(file_type), 
                    headers = headers
                )
                msg = EmailMessage(
                    subject = "report",
                    body = '',
                    from_email = settings.DEFAULT_FROM_EMAIL,
                    to = [user.email],
                )            
                msg.attach('report.pdf', response.rendered_content, 'application/pdf')
                msg.send()    
            return HttpResponse("ok")
        elif file_type == "XLS":
            result = generate_report(request, for_excel = True, report_user = user)
            template = loader.get_template("report.html")
            if emails:
                emails_list = emails.split(",")
                for email in emails_list:
                    email_users = User.objects.filter(email = email)
                    if email_users.count():
                        email_user = email_users[0]
                        result["user"] = email_user
                    context = result
                    html = template.render(context)
                    import pandas as pd
                    # Assign the table data to a Pandas dataframe 
                    table = pd.read_html(html)[0]
                    dir = "%s/reports" % settings.MEDIA_ROOT
                    Path(dir).mkdir(parents=True, exist_ok=True)
                    # Store the dataframe in Excel file
                    filename = "%s/report-%s.xlsx" % (dir, randint(0, 100000))
        #             print(filename)
                    table.to_excel(filename)
                    msg = EmailMessage(
                        subject = "report",
                        body = '',
                        from_email = settings.DEFAULT_FROM_EMAIL,
                        to = [email],
                    )            
                    msg.attach_file(filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    msg.send()
            elif user:    
                context = result
                html = template.render(context)
                import pandas as pd
                # Assign the table data to a Pandas dataframe 
                table = pd.read_html(html)[0]
                dir = "%s/reports" % settings.MEDIA_ROOT
                Path(dir).mkdir(parents=True, exist_ok=True)
                # Store the dataframe in Excel file
                filename = "%s/report-%s.xlsx" % (dir, randint(0, 100000))
    #             print(filename)
                table.to_excel(filename)
                msg = EmailMessage(
                    subject = "report",
                    body = '',
                    from_email = settings.DEFAULT_FROM_EMAIL,
                    to = [user.email],
                )            
                msg.attach_file(filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                msg.send()    
            return HttpResponse("ok")
        elif file_type == "DOCX":
            data, device_type = generate_separate_objects_report(request, report_user = user)
            template_file_name = "%s/templates/%s" % (settings.BASE_DIR, device_type.get_template_file_name(file_type))
            mimetypes.init()
            extension = ".docx"
            extension = extension.lower()
            content_type = ""
            if extension in mimetypes.types_map:
                content_type = mimetypes.types_map[extension]
            if emails:
                emails_list = emails.split(",")
                for email in emails_list:
                    email_users = User.objects.filter(email = email)
                    if email_users.count():
                        email_user = email_users[0]
                        data, device_type = generate_separate_objects_report(request, report_user = email_user)
                    dir = "%s/reports" % settings.MEDIA_ROOT
                    Path(dir).mkdir(parents=True, exist_ok=True)
                    # Store the dataframe in Excel file
                    filename = "%s/report-%s.docx" % (dir, randint(0, 100000))
                    create_docx_report(data, template_file_name, filename, headers = headers)
                    msg = EmailMessage(
                        subject = "report",
                        body = '',
                        from_email = settings.DEFAULT_FROM_EMAIL,
                        to = [email],
                    )            
                    msg.attach_file(filename, content_type)
                    msg.send()
            elif user:    
                dir = "%s/reports" % settings.MEDIA_ROOT
                Path(dir).mkdir(parents=True, exist_ok=True)
                # Store the dataframe in Excel file
                filename = "%s/report-%s.docx" % (dir, randint(0, 100000))
                create_docx_report(data, template_file_name, filename)
                msg = EmailMessage(
                    subject = "report",
                    body = '',
                    from_email = settings.DEFAULT_FROM_EMAIL,
                    to = [user.email],
                )            
                msg.attach_file(filename, content_type)
                msg.send()
            return HttpResponse("ok")            
        elif file_type == "CSV":
            dir = "%s/reports" % settings.MEDIA_ROOT
            Path(dir).mkdir(parents=True, exist_ok=True)
            # Store the dataframe in Excel file
            filename = "%s/report-%s.csv" % (dir, randint(0, 100000))
            with open(filename, "w") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(result["headers"])
                for row in result["values"]:
                    writer.writerow(row.data)
            if emails:
                emails_list = emails.split(",")
                for email in emails_list:
                    msg = EmailMessage(
                        subject = "report",
                        body = '',
                        from_email = settings.DEFAULT_FROM_EMAIL,
                        to = [email],
                    )            
                    msg.attach_file(filename, "text/csv")
                    msg.send()
            elif user:    
                msg = EmailMessage(
                    subject = "report",
                    body = '',
                    from_email = settings.DEFAULT_FROM_EMAIL,
                    to = [user.email],
                )            
                msg.attach_file(filename, "text/csv")
                msg.send()    
            return HttpResponse("ok")            
        return TemplateResponse(request, "report.html", result)

    def get(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)

    def head(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)
    
    
    
