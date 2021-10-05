from django.urls import path
from heatcontrol.api.views import AuthCheckView, LoginView, RegistrationView, CompaniesNamesView,\
    CompaniesListView, CreateCompanyView,\
    CompanyObjectView,\
    CompanyObjectsView, CompanyAddObjectView, UserView,\
    CompanyAddStaffView, CompanyStaffView, CompanyView, AddDeviceView,\
    DevicesView, DeviceView, ModemsView, AddModemView, DeviceModemView, TasksView,\
    TaskView, QueriesView, AddQueryView, QueryView,\
    CompanyObjectModemsView, CompanyObjectAddModemView, DevicesListView,\
    ModemsListView, CompanyDevicesView, CompanyModemsView, ModemView,\
    ModemTasksView, TotalsView, ModemDevicesView,\
    MeteringPoints, AddMeteringPoint, MeteringPointView, DeviceTypesView,\
    AddDEviceTypeView, DeviceTypeView, \
    MeteringPointsDataList, AddMeteringPointData, MeteringPointDataView,\
    MeteringPointTasksView, MeteringPointAddTaskView, ModemQueriesView,\
    MeteringPointQueriesView, UserRolesView, CompanyAddDepartmentView,\
    CompanyDepartmentsView, CompanyDepartmentView, RequestMeteringPointData,\
    SuggestionsFiasView, ModemTypesView, AddModemTypeView, ModemTypeView,\
    CompanyLogoView, UserAvatarView, SuggestionsAddressView,\
    RequestMeteringPointDataByReportType, MeteringPointsDataListByReportType,\
    HeatSupplySchemesView, AddHeatSupplySchemeView, HeatSupplySchemeView,\
    DeviceTimeView, SearchView, MeteringPointHeatSupplySchemesView,\
    AddMeteringPointHeatSupplySchemeView, MeteringPointHeatSupplySchemeView,\
    ReportView, ReportDownloadView, ReportEmailView, CompanyObjectWeatherView,\
    DepartmentTypesView, AddDepartmentTypeView, DepartmentTypeView,\
    CompanyObjectDeviceDataView, SensorTypesView, AddSensorTypeView,\
    SensorTypeView, FlowMeterTypesView, AddFlowMeterTypeView, FlowMeterTypeView,\
    FlowMetersView, AddFlowMeterView, FlowMeterView, SensorsView, AddSensorView,\
    SensorView, AllCompanyObjectsView, CompanyObjectMeteringPointsView


urlpatterns = [
    path('auth_check/', AuthCheckView.as_view(), name='auth_check'),
    path('user/login/', LoginView.as_view(), name='login'),    
    path('user/register/', RegistrationView.as_view(), name='login'),    
    path('users/<int:user_id>/', UserView.as_view(), name='user_view'),    
    path('users/<int:user_id>/avatar/', UserAvatarView.as_view(), name="upload_user_avatar"),
    path('users/roles/', UserRolesView.as_view(), name='user_roles'),    

    path('companies/names/', CompaniesNamesView.as_view(), name='companies_names'),    
    path('companies/list/', CompaniesListView.as_view(), name='companies_list'),    
    path('companies/add/', CreateCompanyView.as_view(), name="company_add"),
    path('companies/<int:company_id>/', CompanyView.as_view(), name="company_view"),
    path('companies/<int:company_id>/logo/', CompanyLogoView.as_view(), name="upload_company_logo"),
    path('companies/<int:company_id>/staff/', CompanyStaffView.as_view(), name="company_staff"),
    path('companies/<int:company_id>/staff/add/', CompanyAddStaffView.as_view(), name="company_add_staff"),
    path('companies/<int:company_id>/departments/add/', CompanyAddDepartmentView.as_view(), name="company_add_department"),
    path('companies/<int:company_id>/departments/', CompanyDepartmentsView.as_view(), name="company_departments"),
    path('companies/<int:company_id>/departments/<int:department_id>/', CompanyDepartmentView.as_view(), name="company_department_view"),
    path('department_types/list/', DepartmentTypesView.as_view(), name='department_types_list'),    
    path('department_types/add/', AddDepartmentTypeView.as_view(), name="add_department_type"),
    path('department_types/<int:type_id>/', DepartmentTypeView.as_view(), name="department_type_view"),
    path('companies/<int:company_id>/objects/add/', CompanyAddObjectView.as_view(), name="company_add_objects"),
    path('company_objects/', AllCompanyObjectsView.as_view(), name="all_company_objects"),
    path('companies/<int:company_id>/objects/', CompanyObjectsView.as_view(), name="company_objects"),
    path('companies/<int:company_id>/objects/<int:object_id>/', CompanyObjectView.as_view(), name="company_object_view"),
    path('companies/<int:company_id>/objects/<int:object_id>/devices/add/', AddDeviceView.as_view(), name="add_device_view"),
    path('companies/<int:company_id>/objects/<int:object_id>/modems/add/', CompanyObjectAddModemView.as_view(), name="company_object_add_modem"),
    path('companies/<int:company_id>/objects/<int:object_id>/devices/', DevicesView.as_view(), name="devices_view"),
    path('companies/<int:company_id>/objects/<int:object_id>/metering_points/', CompanyObjectMeteringPointsView.as_view(), name="company_object_metering_points_view"),
    path('companies/<int:company_id>/objects/<int:object_id>/modems/', CompanyObjectModemsView.as_view(), name="company_object_modems"),
    path('companies/<int:company_id>/objects/<int:object_id>/device_data/', CompanyObjectDeviceDataView.as_view(), name="company_object_device_data"),
    path('companies/<int:company_id>/objects/<int:object_id>/weather/', CompanyObjectWeatherView.as_view(), name="company_object_weathers"),
    path('companies/<int:company_id>/devices/', CompanyDevicesView.as_view(), name="company_devices"),
    path('companies/<int:company_id>/modems/', CompanyModemsView.as_view(), name="company_modems"),
    path('devices/list/',  DevicesListView.as_view(), name="devices_list"),
    path('modems/list/',  ModemsListView.as_view(), name="modems_list"),
    path('modems/<int:modem_id>/',  ModemView.as_view(), name="modem_view"),
    path('devices/<int:device_id>/time/',  DeviceTimeView.as_view(), name="device_time_view"),
    path('devices/<int:device_id>/',  DeviceView.as_view(), name="device_view"),
    path('devices/<int:device_id>/modems/',  ModemsView.as_view(), name="modems_view"),
    path('devices/<int:device_id>/modems/add/',  AddModemView.as_view(), name="add_modem_view"),
    path('devices/<int:device_id>/modems/<int:modem_id>/',  DeviceModemView.as_view(), name="device_modem_view"),
    path('devices/<int:device_id>/sensors/',  SensorsView.as_view(), name="sensors_view"),
    path('devices/<int:device_id>/sensors/add/',  AddSensorView.as_view(), name="add_sensor_view"),
    path('sensors/<int:sensor_id>/',  SensorView.as_view(), name="sensor_view"),
    path('devices/<int:device_id>/flow_meters/',  FlowMetersView.as_view(), name="flow_meters_view"),
    path('devices/<int:device_id>/flow_meters/add/',  AddFlowMeterView.as_view(), name="add_flow_meter_view"),
    path('flow_meters/<int:flow_meter_id>/',  FlowMeterView.as_view(), name="flow_meter_view"),
    path('devices/<int:device_id>/modems/<int:modem_id>/tasks/',  TasksView.as_view(), name="modem_tasks"),
    path('modems/<int:modem_id>/devices/',  ModemDevicesView.as_view(), name="modem_devices_view"),
    path('modems/<int:modem_id>/tasks/',  ModemTasksView.as_view(), name="modem_tasks_view"),
    path('modems/<int:modem_id>/queries/',  ModemQueriesView.as_view(), name="modem_queries_view"),
    path('tasks/<int:task_id>/',  TaskView.as_view(), name="task_view"),
    path('tasks/<int:task_id>/queries/',  QueriesView.as_view(), name="queries_view"),
    path('tasks/<int:task_id>/add_query/',  AddQueryView.as_view(), name="add_query"),
    path('queries/<int:query_id>/',  QueryView.as_view(), name="query_view"),
    path('totals/',  TotalsView.as_view(), name="totals_view"),
    path('devices/<int:device_id>/metering_points/',  MeteringPoints.as_view(), name="metering_points_view"),
    path('devices/<int:device_id>/metering_points/add/',  AddMeteringPoint.as_view(), name="add_metering_point"),
    path('metering_points/<int:point_id>/',  MeteringPointView.as_view(), name="metering_point_view"),
    path('device_types/list/', DeviceTypesView.as_view(), name='device_types_list'),    
    path('device_types/add/', AddDEviceTypeView.as_view(), name="add_device_type"),
    path('device_types/<int:device_type_id>/', DeviceTypeView.as_view(), name="device_type_view"),
    path('modem_types/list/', ModemTypesView.as_view(), name='modem_types_list'),    
    path('modem_types/add/', AddModemTypeView.as_view(), name="add_modem_type"),
    path('modem_types/<int:modem_type_id>/', ModemTypeView.as_view(), name="modem_type_view"),
    path('sensor_types/list/', SensorTypesView.as_view(), name='sensor_types_list'),    
    path('sensor_types/add/', AddSensorTypeView.as_view(), name="add_sensor_type"),
    path('sensor_types/<int:sensor_type_id>/', SensorTypeView.as_view(), name="sensor_type_view"),
    path('flow_meter_types/list/', FlowMeterTypesView.as_view(), name='flow_meter_types_list'),    
    path('flow_meter_types/add/', AddFlowMeterTypeView.as_view(), name="add_flow_meter_type"),
    path('flow_meter_types/<int:flow_meter_type_id>/', FlowMeterTypeView.as_view(), name="flow_meter_type_view"),
    path('metering_points/<int:point_id>/data/',  MeteringPointsDataList.as_view(), name="metering_point_data_list"),
    path('metering_points/<int:point_id>/data/add/',  AddMeteringPointData.as_view(), name="add_metering_point_data"),
    path('metering_points/<int:point_id>/data/request/<str:report_type>/',  RequestMeteringPointDataByReportType.as_view(), name="request_metering_point_data_by_report_type"),
    path('metering_points/<int:point_id>/data/request/',  RequestMeteringPointData.as_view(), name="request_metering_point_data"),
    path('metering_points/<int:point_id>/data/<int:data_id>/',  MeteringPointDataView.as_view(), name="metering_point_data_view"),
    path('metering_points/<int:point_id>/data/<str:report_type>/',  MeteringPointsDataListByReportType.as_view(), name="metering_point_data_list_by_report_type"),
    path('metering_points/<int:point_id>/tasks/',  MeteringPointTasksView.as_view(), name="metering_point_tasks_view"),
    path('metering_points/<int:point_id>/queries/',  MeteringPointQueriesView.as_view(), name="metering_point_queries_view"),
    path('metering_points/<int:point_id>/add_task/',  MeteringPointAddTaskView.as_view(), name="metering_point_add_task"),
    path('suggestions/fias/',  SuggestionsFiasView.as_view(), name="suggestions_fias"),
    path('suggestions/address/',  SuggestionsAddressView.as_view(), name="suggestions_address"),
    path('heat_supply_schemes/list/', HeatSupplySchemesView.as_view(), name='heat_supply_schemes_list'),    
    path('heat_supply_schemes/add/', AddHeatSupplySchemeView.as_view(), name="add_heat_supply_scheme"),
    path('heat_supply_schemes/<int:id>/', HeatSupplySchemeView.as_view(), name="heat_supply_scheme_view"),
    path('heat_supply_schemes/<int:id>/metering_point_parameters/list/', MeteringPointHeatSupplySchemesView.as_view(), name='metering_point_heat_supply_schemes_list'),    
    path('heat_supply_schemes/<int:id>/metering_point_parameters/add/', AddMeteringPointHeatSupplySchemeView.as_view(), name="add_metering_point_heat_supply_scheme"),
    path('heat_supply_schemes/<int:id>/metering_point_parameters/<int:param_id>/', MeteringPointHeatSupplySchemeView.as_view(), name="metering_point_heat_supply_scheme_view"),
    path('search/', SearchView.as_view(), name="search_view"),
    path('report/', ReportView.as_view(), name="report_view"),
    path('report/download/<str:file_type>/', ReportDownloadView.as_view(), name="report_download_view"),
    path('report/send/<str:file_type>/', ReportEmailView.as_view(), name="report_email_view"),

]