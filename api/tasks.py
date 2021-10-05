from celery.task.base import task, periodic_task
from celery.schedules import crontab
from heatcontrol.api.models import CompanyObject, CompanyObjectWeatherData, Task,\
    MeteringPointData, ReportTask, User, BusyDevice
import traceback
import requests
from django.conf import settings
import time
import datetime
from heatcontrol.api.utils import track_object_updated, generate_report,\
    check_mock_reports, generate_separate_objects_report, create_docx_report,\
    create_pdf_report
from django.utils import timezone
from django.db.models import Q
from django.http.request import HttpRequest
from wkhtmltopdf.views import PDFTemplateResponse
from django.core.mail.message import EmailMessage
from django.template import loader
from pathlib import Path
from random import randint
import csv
from heatcontrol.devices.utils import get_device_obj
import mimetypes


@task()
def check_celery():
    print("celery running")
    
    
@periodic_task(run_every=crontab(minute='00', hour='*'))
def get_company_object_weather():
    print("get_company_object_weather")
    for company_object in CompanyObject.objects.filter(deleted = False, address_coords__isnull = False):
        try:
            address_coords = company_object.address_coords
            if len(address_coords) == 2:
                req = requests.get("https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&lang=ru" % (address_coords[0], address_coords[1], settings.OPENWEATHERMAP_API_KEY))
                data = req.json()
                weather_data = CompanyObjectWeatherData(
                    company_object = company_object,
                    data = data,
                )
                weather_data.save()
                print("saved weather data ", weather_data.id)
                time.sleep(1)
            else:
                print("invalid address_coords in company object ", company_object)
        
        except Exception as ex:
            traceback.print_exc()
            

@task()
def execute_task(task_id):
    print("execute_task",  task_id)
    task = Task.objects.get(id = task_id)
    metering_point = task.metering_point
    modem = metering_point.modem
    device = metering_point.device
    if device.status == "DISABLED":
        print("can't execute task, device %s disabled" % device.id)
        return
    busy_devices = BusyDevice.objects.filter(device = device)[:1]
    if busy_devices.count():
        print("device %s is busy, waiting..." % device.id)
        execute_task.apply_async(args=(task_id,), countdown = settings.DEVICE_WAIT_TIME)
        return
    busy_device = BusyDevice(device = device)
    busy_device.save()
    try:
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
        date = device_obj.get_current_time()
        log += "\ndevice time = %s " % date
        log += "\nrequesting data... "
        try:
            input_number = int(metering_point.input_number)
        except Exception as ex:
            input_number = 1
        raw_data, data, request_log, all_data = device_obj.request_data(task.report_type if task.report_type else "DAILY", input_number, metering_point.device.device_type.parameters)
        device_obj.close_connection()
        log += request_log
    #         print("got data:", data)
        #TODO parse data
        metering_point_data = MeteringPointData(
            metering_point = metering_point,
            device_type = device.device_type,
            timestamp = date,
            report_type = task.report_type if task.report_type else "DAILY",
            data = data,
            raw_data = raw_data,
            log = log,
            all_data = all_data,
        )
        metering_point_data.save()
        metering_point_data.calculate_data()
        track_object_updated("Add", None, metering_point_data, metering_point_data.__str__())
        device.set_status("ONLINE")
        print("execute_task completed",  task_id)
    except Exception as ex:
        traceback.print_exc()
        device.set_status("OFFLINE")
    finally:
        busy_devices = BusyDevice.objects.filter(device = device)
        busy_devices.delete()


@periodic_task(run_every = datetime.timedelta(minutes = settings.TASK_EXECUTE_INTERVAL))
def handle_tasks(): 
    print("handle_tasks")
    #сначала ищем задачи, которые непереодические, но надо выполнить в это время
    now = timezone.now()
    date_from = now - datetime.timedelta(minutes = settings.TASK_EXECUTE_INTERVAL / 2)
    date_to = now + datetime.timedelta(minutes = settings.TASK_EXECUTE_INTERVAL / 2)
    tasks = Task.objects.filter(periodic_task = False, time__gte = date_from, time__lt = date_to, deleted = False)
    print("found %s non-periodic tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_task.delay(task.id)
    #ищем периодические задачи
    tasks = Task.objects.filter(periodic_task = True, deleted = False, report_type = "CURRENT")
    print("found %s periodic CURRENT tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_task.delay(task.id)

    previous_hour = date_to - datetime.timedelta(hours = 1)
    tasks = Task.objects.filter(periodic_task = True, report_type = "HOURLY", deleted = False).filter(Q(last_execute_time__isnull = True) | Q(last_execute_time__lt = previous_hour))
    print("found %s periodic HOURLY tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_task.delay(task.id)
        
    time_from = datetime.time(hour = date_from.hour, minute = date_from.minute, second = date_from.second, tzinfo = date_from.tzinfo)
    time_to = datetime.time(hour = date_to.hour, minute = date_to.minute, second = date_to.second, tzinfo = date_to.tzinfo)
    tasks = Task.objects.filter(periodic_task = True, time__time__gte = time_from, time__time__lt = time_to, deleted = False, report_type = "DAILY")
    print("found %s periodic DAILY tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_task.delay(task.id)
    
    previous_month = date_to - datetime.timedelta(days = 30)
    tasks = Task.objects.filter(periodic_task = True, report_type = "MONTHLY", deleted = False).filter(Q(last_execute_time__isnull = True) | Q(last_execute_time__lt = previous_month))
    print("found %s periodic MONTHLY tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_task.delay(task.id)


@task()
def execute_report_task(task_id):
    print("execute_report_task",  task_id)
    task = ReportTask.objects.get(id = task_id)
    result = None
    user = task.user
    emails = task.emails
    if check_mock_reports(task.company_objects.all().values_list("id", flat = True), task.file_type, emails, task.report_type):
        return 

    
    if task.file_type == "CSV":
        result = generate_report(None, report_user = task.user, report_task = task)
    if task.file_type == "PDF":
        request = HttpRequest()
        data, device_type = generate_separate_objects_report(None, report_user = task.user, report_task = task)
        if emails:
            emails_list = emails.split(",")
            for email in emails_list:
                email_users = User.objects.filter(email = email)
                if email_users.count():
                    email_user = email_users[0]
                    data, device_type = generate_separate_objects_report(None, report_user = email_user, report_task = task)
                response = create_pdf_report(
                    request, 
                    data, 
                    device_type.get_template_file_name(task.file_type), 
                    headers = task.headers
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
                device_type.get_template_file_name(task.file_type), 
                headers = task.headers
            )
            msg = EmailMessage(
                subject = "report",
                body = '',
                from_email = settings.DEFAULT_FROM_EMAIL,
                to = [user.email],
            )            
            msg.attach('report.pdf', response.rendered_content, 'application/pdf')
            msg.send()    
        return 
    elif task.file_type == "XLS":
        result = generate_report(None, for_excel = True, report_user = task.user, report_task = task)
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
        return
    elif task.file_type == "DOCX":
        data, device_type = generate_separate_objects_report(None, report_user = task.user, report_task = task)
        template_file_name = "%s/templates/%s" % (settings.BASE_DIR, device_type.get_template_file_name(task.file_type))
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
                    data, device_type = generate_separate_objects_report(None, report_user = email_user, report_task = task)
                dir = "%s/reports" % settings.MEDIA_ROOT
                Path(dir).mkdir(parents=True, exist_ok=True)
                # Store the dataframe in Excel file
                filename = "%s/report-%s.docx" % (dir, randint(0, 100000))
                create_docx_report(data, template_file_name, filename, headers = task.headers)
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
        return
    elif task.file_type == "CSV":
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
    
    
@periodic_task(run_every = datetime.timedelta(minutes = settings.REPORT_TASK_EXECUTE_INTERVAL))
def handle_report_tasks(): 
    print("handle_report_tasks")
    now = timezone.now()
    date_from = now - datetime.timedelta(minutes = settings.TASK_EXECUTE_INTERVAL / 2)
    date_to = now + datetime.timedelta(minutes = settings.TASK_EXECUTE_INTERVAL / 2)
    #ищем периодические задачи
    previous_hour = date_to - datetime.timedelta(hours = 1)
    tasks = ReportTask.objects.filter(send_type = "HOURLY", deleted = False).filter(Q(last_execute_time__isnull = True) | Q(last_execute_time__lt = previous_hour))
    print("found %s report HOURLY tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_report_task.delay(task.id)
        
    time_from = datetime.time(hour = date_from.hour, minute = date_from.minute, second = date_from.second, tzinfo = date_from.tzinfo)
    time_to = datetime.time(hour = date_to.hour, minute = date_to.minute, second = date_to.second, tzinfo = date_to.tzinfo)
    tasks = ReportTask.objects.filter(time__time__gte = time_from, time__time__lt = time_to, deleted = False, report_type = "DAILY")
    print("found %s report DAILY tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_report_task.delay(task.id)
    
    previous_month = date_to - datetime.timedelta(days = 30)
    tasks = ReportTask.objects.filter(report_type = "MONTHLY", deleted = False).filter(Q(last_execute_time__isnull = True) | Q(last_execute_time__lt = previous_month))
    print("found %s report MONTHLY tasks" % tasks.count())
    for task in tasks:
        task.last_execute_time = now
        task.save(update_fields = ["last_execute_time"])
        execute_report_task.delay(task.id)
    