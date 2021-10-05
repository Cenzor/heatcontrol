from rest_framework.test import APITestCase
import json
from heatcontrol.api.models import User, Company, CompanyObject, Device, Modem,\
    Task, Query, MeteringPoint, DeviceType, MeteringPointData, UserPermissions,\
    Department, DataEditHistory, ModemType, HeatSupplyScheme,\
    MeteringPointHeatSupplyScheme, DepartmentType, ReportTask, SensorType,\
    FlowMeterType, Sensor, FlowMeter
from django.conf import settings
import requests
from django.utils import timezone, dateparse
from heatcontrol.api.utils import set_user_role
import datetime

class RegisterTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "user1",
          "password": "qwerty",
          "email": "user1@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin",
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
#         print(response_data)
        self.company_id = response_data["id"]
        department_type = DepartmentType(
            name = "type1",
            role = "system admin",
        )
        department_type.save()
        company = Company.objects.get(id = self.company_id)
        department = Department(
            name = "department1",
            company = company,
            department_type = "type1"
        )
        department.save()
    
    def test_register_user(self):
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": self.company_id,
          "department": "department1",
          "role": "string",
          "phone": "79053923746"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
#         print(response_data)
        user = User.objects.get(id = response_data["user"]["id"])
        self.assertEquals(user.employer.id, self.company_id)
        self.assertEquals(response_data["user"]["username"], "ivan")
        self.assertEquals(response_data["user"]["phone"], user.phone)
        self.assertEquals(response_data["user"]["phone"], "79053923746")
        self.assertEquals(response_data["user"]["company"]["id"], self.company_id)
        self.assertEquals(response_data["user"]["role"], "system admin")
        data_edit_history = DataEditHistory.objects.all().order_by("-id")[0]
        self.assertEqual(data_edit_history.action, "Add")
        self.assertEqual(data_edit_history.model_name, "User")
#         self.assertEqual(data_edit_history.user, user)
        self.assertEqual(data_edit_history.object_name, user.username)
        self.assertEqual(data_edit_history.object_id, user.id)
        self.assertEqual(user.role, "system admin")

class AuthTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin",
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
    
    def test_auth(self):
        request_data = {
          "username": "ivan",
          "password": "qwerty",
        }
        response = self.client.post('/api/user/login/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(response_data["user"]["id"], self.user_id)
        self.assertEquals(response_data["token"], self.token)
        self.assertEquals(response_data["user"]["permissions"]["status_admin_system"], True)
        

class UserViewTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
    
    def test_get_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/users/%s/' % self.user_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(response_data["id"], self.user_id)

    def test_update_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        company = Company(
            name = "company1"
        )
        company.save()
        user = User.objects.get(id = self.user_id)
        user.employer = company
        user.save()
        department_type = DepartmentType(
            name = "type1",
            role = "system admin",
        )
        department_type.save()
        department = Department(
            name = "department1",
            company = company,
            department_type = "type1"
        )
        department.save()
        request_data = {
          "username": "ivan",
          "email": "user1@example.com",
          "first_name": "Ivan1",
          "department": "department1",
        }
        response = self.client.post('/api/users/%s/' % self.user_id, json.dumps(request_data), content_type="application/json")
#         print(response.content)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(response_data["email"], "user1@example.com")
        self.assertEquals(response_data["role"], "system admin")
        user = User.objects.get(id = self.user_id)
        self.assertEquals(user.email, response_data["email"])
        self.assertEquals(user.role, "system admin")
        data_edit_history = DataEditHistory.objects.all().order_by("-id")[0]
        self.assertEqual(data_edit_history.action, "Edit")
        self.assertEqual(data_edit_history.model_name, "User")
        self.assertEqual(data_edit_history.user, user)
        self.assertEqual(data_edit_history.object_name, user.username)
        self.assertEqual(data_edit_history.object_id, user.id)
        self.assertEqual(data_edit_history.data, {
            "email": {
                "old": "user@example.com",
                "new": "user1@example.com",
            },
            "first_name": {
                "old": "Ivan",
                "new": "Ivan1",
            },
            "department": {
                "old": "Department",
                "new": "department1",
            }
        })
        
    def test_delete_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.delete('/api/users/%s/' % self.user_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        user = User.objects.filter(id = self.user_id, deleted = False)
        self.assertEquals(user.count(), 0)
        data_edit_history = DataEditHistory.objects.all().order_by("-id")[0]
        self.assertEqual(data_edit_history.action, "Delete")
        self.assertEqual(data_edit_history.model_name, "User")
        self.assertEqual(data_edit_history.user, User.objects.get(id = self.user_id))
#         self.assertEqual(data_edit_history.object_name, user.username)
        self.assertEqual(data_edit_history.object_id, self.user_id)
        
        
class AddCompanyTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
    
    def test_add_company(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        company_id = response_data["id"]
        self.assertEqual(response_data["name"], "Our Company")
        #adding child company
        request_data = {
          "name": "Company2",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": company_id,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["parent_company_name"], "Our Company")
        

class CompanyViewTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        
    def test_companies_names(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/companies/names/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], self.company_id)
        self.assertEqual(response_data[0]["name"], "Our Company")

    def test_companies_list(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/companies/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], self.company_id)
        self.assertEqual(response_data[0]["name"], "Our Company")
        
    def test_get_company(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/companies/%s/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], self.company_id)
        self.assertEqual(response_data["name"], "Our Company")
        
    def test_update_company(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "email": "email2@example.com",
        }   
        response = self.client.post('/api/companies/%s/' % self.company_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], self.company_id)
        self.assertEqual(response_data["email"], "email2@example.com")
        company = Company.objects.get(id = self.company_id)
        self.assertEqual(response_data["email"], company.email)

    def test_delete_company(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.delete('/api/companies/%s/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        company = Company.objects.filter(id = self.company_id, deleted = False)
        self.assertEquals(company.count(), 0)
        

class CompanyAddStaffTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        
    def test_company_add_staff(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "username": "ivan2",
          "password": "qwerty",
          "email": "sergey.kaluzhskiy@dumpsterrentalsdepot.ca",
          "first_name": "Ivan2",
          "last_name": "Ivanov2",
          "patronymic": "Ivanovich2",
          "company_id": self.company_id,
          "department": "Department",
          "role": "string"
        }
        response = self.client.post('/api/companies/%s/staff/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        user_id = response_data["id"]
        users = User.objects.all()
        self.assertEqual(users.count(), 2)
        company = Company.objects.get(id = self.company_id)
        user = User.objects.get(id = user_id)
        self.assertEquals(user.employer, company)
        self.assertEquals(response_data["company"]["name"], company.name)
        response = self.client.get('/api/companies/%s/' % self.company_id, content_type="application/json")
        response_data = json.loads(response.content)
        self.assertEquals(response_data["employee_count"], 1)
        response = self.client.get('/api/companies/%s/staff/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], user_id)  
        

class CompanyDepartmentsTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        
    def test_company_add_department(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
          "company_id": self.company_id,
        }
        response = self.client.post('/api/companies/%s/departments/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        departments = Department.objects.all()
        self.assertEqual(departments.count(), 1)
        department_id = response_data["id"]
        response = self.client.get('/api/companies/%s/departments/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], department_id)  
        response = self.client.get('/api/companies/%s/departments/%s/' % (self.company_id, department_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], department_id)
        request_data = {
            "name": "string2",
        }
        response = self.client.post('/api/companies/%s/departments/%s/' % (self.company_id, department_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], department_id)
        self.assertEqual(response_data["name"], "string2")
        department = Department.objects.get(id = department_id)
        self.assertEqual(department.name, response_data["name"])
        response = self.client.delete('/api/companies/%s/departments/%s/' % (self.company_id, department_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        department = CompanyObject.objects.filter(id = department_id, deleted = False)
        self.assertEqual(department.count(), 0)
        
        request_data = {
          "name": "parent_department",
          "company_id": self.company_id,
        }
        response = self.client.post('/api/companies/%s/departments/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        department_id = response_data["id"]
        request_data = {
          "name": "child_department",
          "company_id": self.company_id,
          "parent": department_id,
        }
        response = self.client.post('/api/companies/%s/departments/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        child_department_id = response_data["id"]
        self.assertEqual(response_data["parent"], department_id)
        child_department = Department.objects.get(id = child_department_id)
        parent_department = Department.objects.get(id = department_id)
        self.assertEqual(child_department.parent_department, parent_department)


class DepartmentTypesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        
    def test_add_department_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
        }
        response = self.client.post('/api/department_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        modem_types = DepartmentType.objects.all()
        self.assertEqual(modem_types.count(), 1)
        modem_type_id = response_data["id"]
        response = self.client.get('/api/department_types/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], modem_type_id)  
        response = self.client.get('/api/department_types/%s/' % modem_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_type_id)
        request_data = {
            "name": "string2",
        }
        response = self.client.post('/api/department_types/%s/' % modem_type_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_type_id)
        self.assertEqual(response_data["name"], "string2")
        modem_type = DepartmentType.objects.get(id = modem_type_id)
        self.assertEqual(modem_type.name, response_data["name"])
        response = self.client.delete('/api/department_types/%s/' % modem_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        modem_type = DepartmentType.objects.filter(id = modem_type_id, deleted = False)
        self.assertEqual(modem_type.count(), 0)
        department_type = DepartmentType(
            name = "type1",
            role = "system admin",
        )
        department_type.save()
        company = Company(
            name = "company1"
        )
        company.save()
        user = User.objects.get(id = self.user_id)
        user.employer = company
        user.save()
        department = Department(
            name = "department1",
            company = company,
            department_type = str(department_type.id)
        )
        department.save()
        user.department = "department1"
        user.save()
        set_user_role(user)
#         print(user.role)
        self.assertEqual(user.role, "system admin")
        
        
class CompanyObjectsTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        
    def test_company_add_object(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ],
          "heating_season_start_date": "2017-07-21T00:00:00.000Z",
          "heating_season_enabled_date": "2017-07-21T00:00:00.000Z",
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        objects = CompanyObject.objects.all()
        self.assertEqual(objects.count(), 1)
        object_id = response_data["id"]
        date = dateparse.parse_datetime("2017-07-21T00:00:00.000Z")
        self.assertEqual(objects[0].heating_season_start_date, date)
        response = self.client.get('/api/companies/%s/objects/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], object_id)  
        response = self.client.get('/api/company_objects/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], object_id)  
        response = self.client.get('/api/companies/%s/objects/%s/' % (self.company_id, object_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], object_id)
        request_data = {
            "name": "string",
            "mode": "mode2",
        }
        response = self.client.post('/api/companies/%s/objects/%s/' % (self.company_id, object_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], object_id)
        self.assertEqual(response_data["mode"], "mode2")
        company_object = CompanyObject.objects.get(id = object_id)
        self.assertEqual(company_object.mode, response_data["mode"])
        response = self.client.delete('/api/companies/%s/objects/%s/' % (self.company_id, object_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        company_object = CompanyObject.objects.filter(id = object_id, deleted = False)
        self.assertEqual(company_object.count(), 0)
        
        
class DevicesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        self.device_type = DeviceType(
            name = "device_type1",
            parameters = {
                "key": "value"
            }
        )
        self.device_type.save()
        
    def test_add_device(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "device_type_id": self.device_type.id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string",
        }
#         print(request_data)
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        devices = Device.objects.all()
        self.assertEqual(devices.count(), 1)
        device_id = response_data["id"]
        self.assertEqual(devices[0].device_type, self.device_type)
        response = self.client.get('/api/companies/%s/objects/%s/devices/' % (self.company_id, self.object_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], device_id)  
        response = self.client.get('/api/companies/%s/devices/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], device_id)  
        response = self.client.get('/api/devices/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], device_id)  
        response = self.client.get('/api/devices/%s/' % device_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], device_id)
        request_data = {
            "name": "string",
            "serial_number": "number2",
        }
        response = self.client.post('/api/devices/%s/' % device_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], device_id)
        self.assertEqual(response_data["serial_number"], "number2")
        device = Device.objects.get(id = device_id)
        self.assertEqual(device.serial_number, response_data["serial_number"])
        response = self.client.delete('/api/devices/%s/' % device_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        device = Device.objects.filter(id = device_id, deleted = False)
        self.assertEqual(device.count(), 0)
        #пробуем добавить устройство без имени
        request_data = { 
          "company_object_id": self.object_id,
          "device_type_id": self.device_type.id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string",
        }
#         print(request_data)
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        devices = Device.objects.filter(deleted = False)
        self.assertEqual(devices.count(), 1)
        self.assertEqual(devices[0].device_type, self.device_type)

        
class SensorsTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        
    def test_add_sensor(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "device_id": self.device_id,
          "model": "string",
          "modification": "string",
          "value_min": 0,
          "value_max": 0,
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing": True,
          "sealing_number": "string"
        }
        response = self.client.post('/api/devices/%s/sensors/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        sensors = Sensor.objects.all()
        self.assertEqual(sensors.count(), 1)
        sensor_id = response_data["id"]
        response = self.client.get('/api/devices/%s/sensors/' % self.device_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], sensor_id)  
        response = self.client.get('/api/sensors/%s/' % sensor_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], sensor_id)
        request_data = {
            "model": "string2",
        }
        response = self.client.post('/api/sensors/%s/' % sensor_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], sensor_id)
        self.assertEqual(response_data["model"], "string2")
        sensor = Sensor.objects.get(id = sensor_id)
        self.assertEqual(sensor.model, response_data["model"])
        response = self.client.delete('/api/sensors/%s/' % sensor_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        sensor = Sensor.objects.filter(id = sensor_id, deleted = False)
        self.assertEqual(sensor.count(), 0)
        
        
class FlowMetersTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        
    def test_add_flow_meter(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "device_id": self.device_id,
          "model": "string",
          "modification": "string",
          "value_min": 0,
          "value_max": 0,
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing": True,
          "sealing_number": "string"
        }
        response = self.client.post('/api/devices/%s/flow_meters/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        sensors = FlowMeter.objects.all()
        self.assertEqual(sensors.count(), 1)
        sensor_id = response_data["id"]
        response = self.client.get('/api/devices/%s/flow_meters/' % self.device_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], sensor_id)  
        response = self.client.get('/api/flow_meters/%s/' % sensor_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], sensor_id)
        request_data = {
            "model": "string2",
        }
        response = self.client.post('/api/flow_meters/%s/' % sensor_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], sensor_id)
        self.assertEqual(response_data["model"], "string2")
        sensor = FlowMeter.objects.get(id = sensor_id)
        self.assertEqual(sensor.model, response_data["model"])
        response = self.client.delete('/api/flow_meters/%s/' % sensor_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        sensor = FlowMeter.objects.filter(id = sensor_id, deleted = False)
        self.assertEqual(sensor.count(), 0)
        
        
class ModemsTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        
    def test_add_modem(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        add_modem_request_data = request_data
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        modems = Modem.objects.all()
        self.assertEqual(modems.count(), 1)
        modem_id = response_data["id"]
        response = self.client.get('/api/devices/%s/modems/' % self.device_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], modem_id)  
        response = self.client.get('/api/modems/%s/devices/' % modem_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], self.device_id)  
        response = self.client.get('/api/companies/%s/modems/' % self.company_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], modem_id)  
        response = self.client.get('/api/modems/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], modem_id)  
        response = self.client.get('/api/companies/%s/objects/%s/modems/' % (self.company_id, self.object_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], modem_id)  
        response = self.client.get('/api/devices/%s/modems/%s/' % (self.device_id, modem_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_id)
        request_data = {
            "model": "string",
            "serial_number": "number2",
        }
        response = self.client.post('/api/devices/%s/modems/%s/' % (self.device_id, modem_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_id)
        self.assertEqual(response_data["serial_number"], "number2")
        modem = Modem.objects.get(id = modem_id)
        self.assertEqual(modem.serial_number, response_data["serial_number"])
        response = self.client.delete('/api/devices/%s/modems/%s/' % (self.device_id, modem_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        modem = Modem.objects.filter(id = modem_id, deleted = False)
        self.assertEqual(modem.count(), 0)
        # добавляем модем через объект
        response = self.client.post('/api/companies/%s/objects/%s/modems/add/' % (self.company_id, self.object_id), json.dumps(add_modem_request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        modems = Modem.objects.filter(deleted = False)
        self.assertEqual(modems.count(), 1)
        modem_id = response_data["id"]
        response = self.client.get('/api/modems/%s/' % modem_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_id)
        request_data = {
            "model": "string",
            "serial_number": "number2",
        }
        response = self.client.post('/api/modems/%s/' % modem_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_id)
        self.assertEqual(response_data["serial_number"], "number2")
        modem = Modem.objects.get(id = modem_id)
        self.assertEqual(modem.serial_number, response_data["serial_number"])
        response = self.client.delete('/api/modems/%s/' % modem_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        modem = Modem.objects.filter(id = modem_id, deleted = False)
        self.assertEqual(modem.count(), 0)
        
        
class QueriesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "string",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        request_data = {
          "metering_point_id": self.point_id,
          "name": "string",
          "time": "2017-07-21T00:00:00.000Z",
          "periodic_task": True
        }
        response = self.client.post('/api/metering_points/%s/add_task/' % self.point_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.task_id = response_data["id"]
        
    def test_add_query(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "task_id": self.task_id,
          "name": "string",
          "request_date": "2017-07-21T00:00:00.000Z",
          "response_date": "2017-07-21T00:00:00.000Z",
          "request": "string",
          "response": "string",
          "error": False
        }
        response = self.client.post('/api/tasks/%s/add_query/' % self.task_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        query = Query.objects.all()
        self.assertEqual(query.count(), 1)
        query_id = response_data["id"]
        response = self.client.get('/api/tasks/%s/queries/' % self.task_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], query_id)  
        response = self.client.get('/api/modems/%s/queries/' % self.modem_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], query_id)  
        response = self.client.get('/api/metering_points/%s/queries/' % self.point_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], query_id)  
        response = self.client.get('/api/queries/%s/' % query_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], query_id)
        request_data = {
            "name": "string",
            "request": "string1",
        }
        response = self.client.post('/api/queries/%s/' % query_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], query_id)
        self.assertEqual(response_data["request"], "string1")
        query = Query.objects.get(id = query_id)
        self.assertEqual(query.request, response_data["request"])
        response = self.client.delete('/api/queries/%s/' % query_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        query = Query.objects.filter(id = query_id, deleted = False)
        self.assertEqual(query.count(), 0)
        
        
class TotalsTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        company = Company.objects.get(id = self.company_id)
        user = User.objects.get(id = self.user_id)
        user.employer = company
        user.save()
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string",
          "active": True,
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        
    def test_get_totals(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/totals/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
#         print(response_data)
        self.assertEquals(response_data["companies"], 1) 
        self.assertEquals(response_data["users"], 1)  
        self.assertEquals(response_data["company_objects"], 1)  
        self.assertEquals(response_data["modems"], 1)  
        self.assertEquals(response_data["devices"], 1)  
        self.assertEquals(response_data["active_modems"], 1)  
        self.assertEquals(response_data["inactive_modems"], 0)  
        
        
class MeteringPointsTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        
    def test_add_metering_point(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "string",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
#         print(response.content)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        metering_points = MeteringPoint.objects.all()
        self.assertEqual(metering_points.count(), 1)
        point_id = response_data["id"]
        response = self.client.get('/api/devices/%s/metering_points/' % self.device_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], point_id)  
        response = self.client.get('/api/companies/%s/objects/%s/metering_points/' % (self.company_id, self.object_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], point_id)  
        response = self.client.get('/api/metering_points/%s/' % point_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], point_id)
        request_data = {
            "name": "string",
            "auto_polling": False,
        }
        response = self.client.post('/api/metering_points/%s/' % point_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], point_id)
        self.assertEqual(response_data["auto_polling"], False)
        metering_point = MeteringPoint.objects.get(id = point_id)
        self.assertEqual(metering_point.auto_polling, response_data["auto_polling"])
        response = self.client.delete('/api/metering_points/%s/' % point_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        metering_point = MeteringPoint.objects.filter(id = point_id, deleted = False)
        self.assertEqual(metering_point.count(), 0)


class DeviceTypesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        
    def test_add_device_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
          "parameters": {
              "key": "value"
          }
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        device_types = DeviceType.objects.all()
        self.assertEqual(device_types.count(), 1)
        device_type_id = response_data["id"]
        response = self.client.get('/api/device_types/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], device_type_id)  
        response = self.client.get('/api/device_types/%s/' % device_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], device_type_id)
        request_data = {
            "name": "string",
            "parameters": {
                "key": "value",
                "key2": "value2"
            }
        }
        response = self.client.post('/api/device_types/%s/' % device_type_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], device_type_id)
        self.assertEqual(response_data["parameters"]["key2"], "value2")
        device_type = DeviceType.objects.get(id = device_type_id)
        self.assertEqual(device_type.parameters["key2"], response_data["parameters"]["key2"])
        response = self.client.delete('/api/device_types/%s/' % device_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        device_type = DeviceType.objects.filter(id = device_type_id, deleted = False)
        self.assertEqual(device_type.count(), 0)
        

class MeteringPointsDataTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "name": "string",
          "parameters": {
              "key": "value"
          }
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_type_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "string",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        
    def test_add_metering_point_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "metering_point_id": self.point_id,
          "device_type_id": self.device_type_id,
          "timestamp": "2017-07-21T00:00:00.000Z",
          "data": {
              "key": "Value"
          }
        }
        response = self.client.post('/api/metering_points/%s/data/add/' % self.point_id, json.dumps(request_data), content_type="application/json")
#         print(response.content)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        metering_point_data = MeteringPointData.objects.all()
        self.assertEqual(metering_point_data.count(), 1)
        data_id = response_data["id"]
        response = self.client.get('/api/metering_points/%s/data/' % self.point_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], data_id)  
        response = self.client.get('/api/metering_points/%s/data/%s/' % (self.point_id, data_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], data_id)
        request_data = {
            "data": {
                "key": "value",
                "key2": "value2"
            }
        }
        response = self.client.post('/api/metering_points/%s/data/%s/' % (self.point_id, data_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
#         print(response_data)
        self.assertEqual(response_data["id"], data_id)
        self.assertEqual(response_data["data"]["key2"], "value2")
        metering_point_data = MeteringPointData.objects.get(id = data_id)
        self.assertEqual(metering_point_data.data["key2"], response_data["data"]["key2"])
        response = self.client.delete('/api/metering_points/%s/data/%s/' % (self.point_id, data_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        metering_point_data = MeteringPointData.objects.filter(id = data_id, deleted = False)
        self.assertEqual(metering_point_data.count(), 0)
        
        
class MeteringPointsTaskTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "name": "string",
          "parameters": {
              "key": "value"
          }
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_type_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "string",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        
    def test_add_task(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "metering_point_id": self.point_id,
          "name": "string",
          "time": "2017-07-21T00:00:00.000Z",
          "periodic_task": True
        }
        response = self.client.post('/api/metering_points/%s/add_task/' % self.point_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        tasks = Task.objects.all()
        self.assertEqual(tasks.count(), 1)
        task_id = response_data["id"]
        response = self.client.get('/api/metering_points/%s/tasks/' % self.point_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], task_id)  
        response = self.client.get('/api/devices/%s/modems/%s/tasks/' % (self.device_id, self.modem_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], task_id)  
        response = self.client.get('/api/modems/%s/tasks/' % self.modem_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], task_id)  
        response = self.client.get('/api/tasks/%s/' % task_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], task_id)
        request_data = {
            "name": "string",
            "periodic_task": False,
        }
        response = self.client.post('/api/tasks/%s/' % task_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], task_id)
        self.assertEqual(response_data["periodic_task"], False)
        task = Task.objects.get(id = task_id)
        self.assertEqual(task.periodic_task, response_data["periodic_task"])
        response = self.client.delete('/api/tasks/%s/' % task_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        task = Task.objects.filter(id = task_id, deleted = False)
        self.assertEqual(task.count(), 0)
        request_data = {
          "modem_id": self.modem_id,
          "name": "string",
          "time": "2017-07-21T00:00:00.000Z",
          "periodic_task": True
        }


class UserRolesTest(APITestCase):
    def test_user_roles(self):
        response = self.client.get('/api/users/roles/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
#         print(response.content)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data),  4)
        permissions = UserPermissions.objects.all()
        self.assertEqual(permissions.count(),  5)
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "Админ системы"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/users/roles/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
#         print(response.content)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data),  5)
        request_data = {
          "username": "ivan2",
          "password": "qwerty",
          "email": "user2@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "Менеджер приборов учета"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/api/users/roles/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
#         print(response.content)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data),  1)
        
        
class ModemTypesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        
    def test_add_modem_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
        }
        response = self.client.post('/api/modem_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        modem_types = ModemType.objects.all()
        self.assertEqual(modem_types.count(), 1)
        modem_type_id = response_data["id"]
        response = self.client.get('/api/modem_types/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], modem_type_id)  
        response = self.client.get('/api/modem_types/%s/' % modem_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_type_id)
        request_data = {
            "name": "string2",
        }
        response = self.client.post('/api/modem_types/%s/' % modem_type_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], modem_type_id)
        self.assertEqual(response_data["name"], "string2")
        modem_type = ModemType.objects.get(id = modem_type_id)
        self.assertEqual(modem_type.name, response_data["name"])
        response = self.client.delete('/api/modem_types/%s/' % modem_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        modem_type = ModemType.objects.filter(id = modem_type_id, deleted = False)
        self.assertEqual(modem_type.count(), 0)
        
        
class SensorTypesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        
    def test_add_sensor_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
        }
        response = self.client.post('/api/sensor_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        sensor_types = SensorType.objects.all()
        self.assertEqual(sensor_types.count(), 1)
        sensor_type_id = response_data["id"]
        response = self.client.get('/api/sensor_types/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], sensor_type_id)  
        response = self.client.get('/api/sensor_types/%s/' % sensor_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], sensor_type_id)
        request_data = {
            "name": "string2",
        }
        response = self.client.post('/api/sensor_types/%s/' % sensor_type_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], sensor_type_id)
        self.assertEqual(response_data["name"], "string2")
        sensor_type = SensorType.objects.get(id = sensor_type_id)
        self.assertEqual(sensor_type.name, response_data["name"])
        response = self.client.delete('/api/sensor_types/%s/' % sensor_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        sensor_type = SensorType.objects.filter(id = sensor_type_id, deleted = False)
        self.assertEqual(sensor_type.count(), 0)
        
        
class FlowMeterTypesTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        
    def test_add_flow_meter_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
        }
        response = self.client.post('/api/flow_meter_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        flow_meter_types = FlowMeterType.objects.all()
        self.assertEqual(flow_meter_types.count(), 1)
        flow_meter_type_id = response_data["id"]
        response = self.client.get('/api/flow_meter_types/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], flow_meter_type_id)  
        response = self.client.get('/api/flow_meter_types/%s/' % flow_meter_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], flow_meter_type_id)
        request_data = {
            "name": "string2",
        }
        response = self.client.post('/api/flow_meter_types/%s/' % flow_meter_type_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], flow_meter_type_id)
        self.assertEqual(response_data["name"], "string2")
        flow_meter_type = FlowMeterType.objects.get(id = flow_meter_type_id)
        self.assertEqual(flow_meter_type.name, response_data["name"])
        response = self.client.delete('/api/flow_meter_types/%s/' % flow_meter_type_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        flow_meter_type = FlowMeterType.objects.filter(id = flow_meter_type_id, deleted = False)
        self.assertEqual(flow_meter_type.count(), 0)
        
        
class HeatSupplySchemeTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        
    def test_add_heat_supply_scheme(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "string",
          "user_id": self.user_id,
          "data": {
              "key": "value"
          }
        }
        response = self.client.post('/api/heat_supply_schemes/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        objs = HeatSupplyScheme.objects.all()
        self.assertEqual(objs.count(), 1)
        obj_id = response_data["id"]
        response = self.client.get('/api/heat_supply_schemes/list/', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], obj_id)  
        response = self.client.get('/api/heat_supply_schemes/%s/' % obj_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], obj_id)
        request_data = {
            "name": "string2",
        }
        response = self.client.post('/api/heat_supply_schemes/%s/' % obj_id, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], obj_id)
        self.assertEqual(response_data["name"], "string2")
        obj = HeatSupplyScheme.objects.get(id = obj_id)
        self.assertEqual(obj.name, response_data["name"])
        response = self.client.delete('/api/heat_supply_schemes/%s/' % obj_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        obj = HeatSupplyScheme.objects.filter(id = obj_id, deleted = False)
        self.assertEqual(obj.count(), 0)


class SearchTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Теплосила",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        company = Company.objects.get(id = self.company_id)
        user = User.objects.get(id = self.user_id)
        user.employer = company
        user.save()
        request_data = {
          "name": "company object 1",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "device 1",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "my modem",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string",
          "active": True,
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "my metering point",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        
    def test_search(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        #общий поиск
        response = self.client.get('/api/search/?query=ivan', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["users"]), 1)
        self.assertEquals(response_data["users"][0]["id"], self.user_id)
        response = self.client.get('/api/search/?query=sdfasdfasdfsadfd', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["users"]), 0)
        response = self.client.get('/api/search/?query=%s' % requests.utils.quote("Теплосила"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["companies"]), 1)
        self.assertEquals(response_data["companies"][0]["id"], self.company_id)
        response = self.client.get('/api/search/?query=%s' % requests.utils.quote("company object 1"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["company_objects"]), 1)
        self.assertEquals(response_data["company_objects"][0]["id"], self.object_id)
        response = self.client.get('/api/search/?query=%s' % requests.utils.quote("device 1"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["devices"]), 1)
        self.assertEquals(response_data["devices"][0]["id"], self.device_id)
        response = self.client.get('/api/search/?query=%s' % requests.utils.quote("my modem"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["modems"]), 1)
        self.assertEquals(response_data["modems"][0]["id"], self.modem_id)
        response = self.client.get('/api/search/?query=%s' % requests.utils.quote("my metering point"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["metering_points"]), 1)
        self.assertEquals(response_data["metering_points"][0]["id"], self.point_id)
        #поиск при помощи фильтров
        response = self.client.get('/api/search/?query=ivan?filter=users', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["users"]), 1)
        self.assertEquals(response_data["users"][0]["id"], self.user_id)
        response = self.client.get('/api/search/?query=sdfasdfasdfsadfd?filter=users', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["users"]), 0)
        response = self.client.get('/api/search/?query=%s&filter=companies' % requests.utils.quote("Теплосила"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["companies"]), 1)
        self.assertEquals(response_data["companies"][0]["id"], self.company_id)
        response = self.client.get('/api/search/?query=%s&filter=company_objects' % requests.utils.quote("company object 1"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["company_objects"]), 1)
        self.assertEquals(response_data["company_objects"][0]["id"], self.object_id)
        response = self.client.get('/api/search/?query=%s&filter=devices' % requests.utils.quote("device 1"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["devices"]), 1)
        self.assertEquals(response_data["devices"][0]["id"], self.device_id)
        response = self.client.get('/api/search/?query=%s&filter=modems' % requests.utils.quote("my modem"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["modems"]), 1)
        self.assertEquals(response_data["modems"][0]["id"], self.modem_id)
        response = self.client.get('/api/search/?query=%s&filter=metering_points' % requests.utils.quote("my metering point"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["metering_points"]), 1)
        self.assertEquals(response_data["metering_points"][0]["id"], self.point_id)
        device_type = DeviceType(name = "device_type 1")
        device_type.save()
        device = Device.objects.get(id = self.device_id)
        device.device_type = device_type
        device.save()
        response = self.client.get('/api/search/?query=%s&filter=devices' % requests.utils.quote("device_type 1"), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data["devices"]), 1)
        self.assertEquals(response_data["devices"][0]["id"], self.device_id)
                  
#         self.assertEquals(response_data["companies"], 1) 
#         self.assertEquals(response_data["company_objects"], 1)  
#         self.assertEquals(response_data["modems"], 1)  
#         self.assertEquals(response_data["devices"], 1)  


class MeteringPointsHeatSupplySchemeTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "name": "string",
          "parameters": {
              "key": "value"
          }
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_type_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "string",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        request_data = {
          "name": "string",
          "user_id": self.user_id,
          "data": {
              "key": "value"
          }
        }
        response = self.client.post('/api/heat_supply_schemes/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        objs = HeatSupplyScheme.objects.all()
        self.assertEqual(objs.count(), 1)
        self.heat_supply_scheme_id = response_data["id"]
        
    def test_add_metering_point_heat_supply_scheme(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "metering_point_id": self.point_id,
          "heat_supply_scheme_id": self.heat_supply_scheme_id,
          "parameters": {
              "key": "Value"
          }
        }
        response = self.client.post('/api/heat_supply_schemes/%s/metering_point_parameters/add/' % self.heat_supply_scheme_id, json.dumps(request_data), content_type="application/json")
#         print(response.content)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        mp_obj = MeteringPointHeatSupplyScheme.objects.all()
        self.assertEqual(mp_obj.count(), 1)
        mp_obj_id = response_data["id"]
        response = self.client.get('/api/heat_supply_schemes/%s/metering_point_parameters/list/' % self.heat_supply_scheme_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), 1)
        self.assertEquals(response_data[0]["id"], mp_obj_id)  
        response = self.client.get('/api/heat_supply_schemes/%s/metering_point_parameters/%s/' % (self.heat_supply_scheme_id, mp_obj_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], mp_obj_id)
        request_data = {
            "parameters": {
                "key": "value",
                "key2": "value2"
            }
        }
        response = self.client.post('/api/heat_supply_schemes/%s/metering_point_parameters/%s/' % (self.heat_supply_scheme_id, mp_obj_id), json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
#         print(response_data)
        self.assertEqual(response_data["id"], mp_obj_id)
        self.assertEqual(response_data["parameters"]["key2"], "value2")
        mp_obj = MeteringPointHeatSupplyScheme.objects.get(id = mp_obj_id)
        self.assertEqual(mp_obj.parameters["key2"], response_data["parameters"]["key2"])
        response = self.client.delete('/api/heat_supply_schemes/%s/metering_point_parameters/%s/' % (self.heat_supply_scheme_id, mp_obj_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        mp_obj = MeteringPointHeatSupplyScheme.objects.filter(id = mp_obj_id, deleted = False)
        self.assertEqual(mp_obj.count(), 0)



class ReportTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Теплосила",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        company = Company.objects.get(id = self.company_id)
        user = User.objects.get(id = self.user_id)
        user.employer = company
        user.save()
        request_data = {
          "name": "company object 1",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = {
          "name": "string",
          "parameters": ["header1", "header2"]
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.device_type_id = response_data["id"]
        request_data = { 
          "name": "device 1",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string",
          "device_type_id": self.device_type_id,
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "my modem",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string",
          "active": True,
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "my metering point",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        metering_point_data = MeteringPointData(
            report_type = "DAILY",
            metering_point = MeteringPoint.objects.get(id = self.point_id),
            device_type = DeviceType.objects.get(id = self.device_type_id),
            timestamp = timezone.now(),
            data = ["value1", "value2"]
        )
        metering_point_data.save()
        self.metering_point_data_id = metering_point_data.id
        
    def test_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        #общий поиск
        response = self.client.get('/api/report/?objects=%s&report_type=DAILY' % self.object_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
#         print(response_data)
        self.assertEquals(response_data["headers"], ["header1", "header2"])
        self.assertEquals(len(response_data["values"]), 1)
        self.assertEquals(response_data["values"][0]["data"], ["value1", "value2"])
        
        
class ReportTaskTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Теплосила",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        company = Company.objects.get(id = self.company_id)
        user = User.objects.get(id = self.user_id)
        user.employer = company
        user.save()
        request_data = {
          "name": "company object 1",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = {
          "name": "string",
          "parameters": ["t1", "t2", "dt", "V1", "M1", "V2", "M2", "P1", "P2", "Q\u043e", "B\u041dP", "BOC", "\u041d\u0421"]
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.device_type_id = response_data["id"]
        request_data = { 
          "name": "device 1",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string",
          "device_type_id": self.device_type_id,
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "my modem",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string",
          "active": True,
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "my metering point",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        metering_point_data = MeteringPointData(
            report_type = "DAILY",
            metering_point = MeteringPoint.objects.get(id = self.point_id),
            device_type = DeviceType.objects.get(id = self.device_type_id),
            timestamp = timezone.now(),
            data = ["0.00", "0.00", "0.00", 0, "0.00", 0, "0.00", 7.0, 7.0, "0.00", 0, 1, "0.00"]
        )
        metering_point_data.save()
        self.metering_point_data_id = metering_point_data.id
        
    def test_create_report_task(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        #общий поиск
        response = self.client.get('/api/report/send/PDF/?objects=%s&report_type=DAILY&periodic_task=true&send_type=HOURLY&username=ivan&time=2017-07-21T00:00:00.000Z' % self.object_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        report_tasks = ReportTask.objects.all()
        self.assertEquals(report_tasks.count(), 1)
        task = report_tasks[0]
        self.assertEquals(task.user.id, self.user_id)
        self.assertEquals(task.company_objects.all()[0].id, self.object_id)
        self.assertEquals(task.file_type, "PDF")
        self.assertEquals(task.send_type, "HOURLY")
        self.assertEquals(task.report_type, "DAILY")
        response = self.client.get('/api/report/send/XLS/?objects=%s&report_type=DAILY&periodic_task=true&send_type=HOURLY&emails=user@example.com,user2.example.com&time=2017-07-21T00:00:00.000Z' % self.object_id, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        report_tasks = ReportTask.objects.all().order_by("-id")
        self.assertEquals(report_tasks.count(), 2)
        task = report_tasks[0]
        self.assertEquals(task.emails, "user@example.com,user2.example.com")
        self.assertEquals(task.company_objects.all()[0].id, self.object_id)
        self.assertEquals(task.file_type, "XLS")
        self.assertEquals(task.send_type, "HOURLY")
        self.assertEquals(task.report_type, "DAILY")
        
        
class CompanyObjectDeviceDataTest(APITestCase):
    def setUp(self):
        permissions = UserPermissions(
            role = "company_admin",
            status_admin_system = True,
        )
        permissions.save()
        request_data = {
          "username": "ivan",
          "password": "qwerty",
          "email": "user@example.com",
          "first_name": "Ivan",
          "last_name": "Ivanov",
          "patronymic": "Ivanovich",
          "company_id": 0,
          "department": "Department",
          "role": "company_admin"
        }
        response = self.client.post('/api/user/register/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.token = response_data["token"]
        self.user_id = response_data["user"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        request_data = {
          "name": "Our Company",
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "company_type": "производитель оборудования",
          "inn": "string",
          "phone": 79051234567,
          "fax": 79051234567,
          "email": "string",
          "parent_company_id": 0,
          "created_date": "2017-07-21T00:00:00.000Z",
          "tariff": "string",
          "departments": [
            "string"
          ],
          "tags": [
            "string"
          ]
        }   
        response = self.client.post('/api/companies/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.company_id = response_data["id"]
        request_data = {
          "name": "string",
          "company_id": self.company_id,
          "address": "Russia, Moscov, Kremlin, 1",
          "address_coords": [
            48.701604,
            44.505872
          ],
          "object_type": "string",
          "mode": "string",
          "mode_switch_date": "2017-07-21T00:00:00.000Z",
          "timezone": "string",
          "fias": "string",
          "note": "string",
          "tags": [
            "string"
          ]
        }
        response = self.client.post('/api/companies/%s/objects/add/' % self.company_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.object_id = response_data["id"]
        request_data = { 
          "name": "string",
          "company_object_id": self.object_id,
          "serial_number": "string",
          "network_address": "string",
          "modification": "string",
          "speed": 0,
          "service_company": "string",
          "data_format": "string",
          "channel": "string",
          "driver_version": "string",
          "current_check_date": "2017-07-21T00:00:00.000Z",
          "next_check_date": "2017-07-21T00:00:00.000Z",
          "sealing_date": "2017-07-21T00:00:00.000Z",
          "device_time": "2017-07-21T00:00:00.000Z",
          "gis_number": "string",
          "device_id": "string",
          "accounting_type": "string",
          "owner": "string",
          "notes": "string"
        }
        response = self.client.post('/api/companies/%s/objects/%s/devices/add/' % (self.company_id, self.object_id), json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_id = response_data["id"]
        request_data = {
          "model": "string",
          "device_id": 1,
          "serial_number": "string",
          "phone": "string",
          "auto_off": True,
          "apn": "string",
          "speed_code1": 0,
          "speed_code2": 0,
          "speed_code3": 0,
          "allow_connection": True,
          "connection_string": "string",
          "edge_enabled": True,
          "firmware_version": "string",
          "gps_class": "string",
          "gprs_setings_setup": "string",
          "sim_identifier": "string",
          "device_identifier": "string",
          "interface_code1": "string",
          "interface_code2": "string",
          "interface_code3": "string",
          "login": "string",
          "password": "string",
          "operator": "string",
          "signal_level": 0,
          "sms_center": "string",
          "imei": "string"
        }
        response = self.client.post('/api/devices/%s/modems/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.modem_id = response_data["id"]
        request_data = {
          "name": "string",
          "parameters": ["t1", "t2", "dt", "V1", "M1", "V2", "M2", "P1", "P2", "Q\u043e", "B\u041dP", "BOC", "\u041d\u0421"],
        }
        response = self.client.post('/api/device_types/add/', json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.device_type_id = response_data["id"]
        request_data = {
          "company_object_id": self.object_id,
          "modem_id": self.modem_id,
          "device_id": self.device_id,
          "name": "string",
          "resource": "string",
          "destination": "string",
          "heating_system": "string",
          "hot_water_system": "string",
          "tu_location": "string",
          "input_output": "string",
          "metering_scheme": "string",
          "scheme_type": "string",
          "report_template": "string",
          "point_id": "string",
          "point_id_additional": "string",
          "point_id_additional1": "string",
          "auto_polling": True,
          "approved_from": "2017-07-21T00:00:00.000Z",
          "approved_to": "2017-07-21T00:00:00.000Z",
          "device_time": "string",
          "heat_calculation_formula": "string",
          "transit_characteristics": "string",
          "unloading_transit": "string",
          "billing_from": "2017-07-21T00:00:00.000Z",
          "billing_to": "2017-07-21T00:00:00.000Z",
          "input_number": "string",
          "notes": "string"
        }
        response = self.client.post('/api/devices/%s/metering_points/add/' % self.device_id, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.point_id = response_data["id"]
        request_data = {
          "metering_point_id": self.point_id,
          "device_type_id": self.device_type_id,
          "timestamp": "2017-07-21T00:00:00.000Z",
          "report_type": "HOURLY",
          "data": ["0.00", "0.00", "0.00", 0, "0.00", 0, "0.00", 7.0, 7.0, "0.00", 0, 1, "0.00"]
        }
        response = self.client.post('/api/metering_points/%s/data/add/' % self.point_id, json.dumps(request_data), content_type="application/json")
#         print(response.content)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.data_id = response_data["id"]
        
    def test_get_company_object_device_data(self):
        metering_point_data = MeteringPointData.objects.get(id = self.data_id)
        metering_point_data.calculate_data()
#         print(metering_point_data.calculated_data)
        self.assertEqual(len(metering_point_data.calculated_data), 9)
        response = self.client.get('/api/companies/%s/objects/%s/device_data/' % (self.company_id, self.object_id), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["object"]["id"], self.object_id)
        datas = response_data["last_hour_datas"]
        self.assertEqual(len(datas), 1)
        self.assertEqual(datas[0]["id"], self.data_id)
        