import xlsxwriter
from xlsxwriter.worksheet import Worksheet


def get_difference(value1, value2):
    try:
        result = abs(value1 - value2)
    except TypeError as ex:
        print(ex)
        return None
    return result


def get_discharge(values):
    v_sup = []
    v_ret = []
    t_total = 0
    for value in values:
        all_data = value.all_data
        if not all_data:
            continue
        v_sup.append(all_data.get('v1'))
        v_ret.append(all_data.get('v2'))
        if 'th' in all_data.keys():
            t_total += all_data.get('th')
    v_sup_res = max(v_sup) - min(v_sup) if v_sup else 0
    v_ret_res = max(v_ret) - min(v_ret) if v_ret else 0
    return v_sup_res, v_ret_res, t_total


def create_table(values, parameters, numbers_format, wrap_format):
    data = []
    columns = [
        {'header': p[1], 'format': numbers_format, 'header_format': wrap_format} for p in parameters
    ]
    columns.insert(0, {'header': u'Время'})

    for value in values:
        all_data = value.all_data
        if not all_data:
            continue
        row = [value.timestamp.strftime('%d.%m.%Y %H:%M:%S'), ]
        for param in parameters:
            if param[0] in all_data.keys():
                row.append(all_data[param[0]])
            elif param[0] == 'dt':
                row.append(get_difference(all_data['t1'], all_data['t2']))
            elif param[0] == 'dp':
                if 'p1' in all_data.keys():
                    row.append(get_difference(all_data['p1'], all_data['p2']))
                elif 'P1' in all_data.keys() and 'P2' in all_data.keys():
                    row.append(get_difference(all_data['P1'], all_data['P2']))
                else:
                    row.append('--')
            else:
                row.append('--')
        data.append(row)

    result = {
        'data': data,
        'columns': columns,
        'first_column': True,
        'banded_rows': True,
        'autofilter': False,
        'style': 'Table Style Light 15'
    }

    return result


def get_parameters(default_parameters, headers):
    if headers:
        parameters = []
        headers = list(map(str.lower, headers))
        for p in default_parameters:
            if p[0].lower() in headers:
                parameters.append(p)
    else:
        parameters = default_parameters
    return parameters


def get_title(title, date_from=None, date_to=None):
    if date_from and date_to:
        return f'{title}\nза период c {date_from.strftime("%d.%m.%Y")} по {date_to.strftime("%d.%m.%Y")}'
    else:
        return title


def create_excel_report(data: dict, filename: str):
    company_objects = data.get('company_objects')
    report_type = data.get('report_type')
    date = data.get('date').strftime('%d.%m.%Y')
    user = data.get('user')
    headers = data.get('headers', None)
    date_from = data.get('date_from')
    date_to = data.get('date_to')
    workbook = xlsxwriter.Workbook(filename)
    workbook.formats[0].set_font_name('Courier New')
    workbook.formats[0].set_text_wrap()

    class WorkbookFormats:
        head_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'font_name': 'Courier New',
            'text_wrap': True
        })
        text_right_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'font_size': 11,
            'font_name': 'Courier New'
        })
        text_left_format = workbook.add_format({
            'align': 'left',
            'font_size': 11,
            'font_name': 'Courier New',
            'text_wrap': True
        })
        number_format = workbook.add_format({
            'num_format': '0.00',
            'font_name': 'Courier New',
        })
        wrap_format = workbook.add_format({
            'text_wrap': True,
        })
        address_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'vjustify',
            'align': 'left',
            'font_size': 11,
            'font_name': 'Courier New',
        })

    worksheets = {
        'vist': vist_worksheet,
        'carat307': carat_worksheet,
        'ТВ-7': tv7_worksheet,
        'ВКТ-7': vkt7_worksheet,
        'TSRV043': tsrv043_worksheet,
        'sa94': sa94_worksheet,
        'spt961m': None,
        'elf04': None,
    }

    for cp in company_objects:
        company_object = cp.get('company_object')
        metering_points = cp.get('metering_points')
        for mp in metering_points:
            device = mp.get('device')
            if not headers:
                headers = mp.get('headers')
            metering_point = mp.get('metering_point')

            worksheet_name = f'{company_object.name}_{metering_point.id}'
            worksheet = workbook.add_worksheet(name=worksheet_name)

            worksheets[device.device_type.model](worksheet, WorkbookFormats, mp, device,
                                                 date, user, date_from, date_to, headers, report_type)

    workbook.close()


def vist_worksheet(worksheet: Worksheet, w_format, metering_point, device, date,
                   user, date_from=None, date_to=None, headers=None, report_type='DAILY'):
    values = metering_point.get('values')
    mp = metering_point.get('metering_point')
    report_date = mp.approved_from.strftime('%d.%m.%Y') if mp.approved_from else None
    report_time = ...

    default_parameters = [
        ('q', 'Qтепл \n[Гкал]', 1),
        ('t1', 'Tпод \n[oC]', 2),
        ('t2', 'Tобp \n[oC]', 3),
        ('dt', 'dT \n[oC]', 4),
        ('t3', 'Tп \n[oC]', 5),
        ('m1', 'M1 \n[Т]', 6),
        ('v1', 'Vпод \n[м3]', 7),
        ('m2', 'M2 \n[Т]', 8),
        ('v2', 'Vобр \n[м3]', 9),
        ('v3', 'V3 \n[м3]', 10),
        ('p1', 'Pпод \n[ат]', 11),
        ('p2', 'Pобр \n[ат]', 12),
        ('dp', 'dP \n[ат]', 13),
        ('th', 'Tнар \n[час]', 14)
    ]

    parameters = get_parameters(default_parameters, headers)

    title = {
        'CURRENT': u'Протокол учета текущих показаний тепловой энергии и теплоносителя',
        'HOURLY': u'Часовой протокол учета тепловой энергии и теплоносителя',
        'DAILY': u'Дневной протокол учета тепловой энергии и теплоносителя',
        'MONTHLY': u'Месячный протокол учета тепловой энергии и теплоносителя',
    }

    worksheet.set_default_row(20)
    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:O', 12)
    worksheet.set_row(15, 30)
    worksheet.set_row(5, 30)

    worksheet.merge_range('A1:O3', get_title(title[report_type], date_from, date_to), w_format.head_format)

    worksheet.merge_range('A4:B4', u'Название потребителя: ', w_format.text_right_format)
    worksheet.merge_range('C4:E4', device.company_object.name, w_format.text_left_format)
    worksheet.merge_range('A5:B5', u'Абонент: ', w_format.text_right_format)
    worksheet.merge_range('C5:K5', '', w_format.text_left_format)
    worksheet.merge_range('A6:B6', u'Адрес потребителя: ', w_format.text_right_format)
    worksheet.merge_range('C6:E6', device.company_object.address, w_format.text_left_format)
    worksheet.merge_range('A7:B7', u'Телефон: ', w_format.text_right_format)
    worksheet.merge_range('C7:E7', user.phone, w_format.text_left_format)
    worksheet.merge_range('A8:B8', u'Ответственное лицо: ', w_format.text_right_format)
    worksheet.merge_range('C8:E8', f'{user.first_name} {user.last_name}', w_format.text_left_format)

    worksheet.merge_range('A9:O9', '')

    worksheet.merge_range('A10:B10', u'Наименование прибора: ', w_format.text_right_format)
    worksheet.merge_range('C10:E10', device.__str__(), w_format.text_left_format)
    worksheet.merge_range('A11:B11', u'Серийный номер: ', w_format.text_right_format)
    worksheet.merge_range('C11:E11', device.serial_number, w_format.text_left_format)
    worksheet.merge_range('A12:B12', u'Отчетное число месяца: ', w_format.text_right_format)
    worksheet.merge_range('C12:E12', report_date, w_format.text_left_format)
    worksheet.merge_range('A13:B13', u'Отчетное время: ', w_format.text_right_format)
    worksheet.merge_range('C13:E13', '', w_format.text_left_format)

    # mp = metering_point.get('metering_point')
    # worksheet.merge_range('A12:B12', u'Точка учета: ', w_format.text_right_format)
    # worksheet.merge_range('C12:E12', mp.name, w_format.text_left_format)

    worksheet.merge_range('A14:B14', u'Дата формирования отчета: ', w_format.text_right_format)
    worksheet.merge_range('C14:E14', date, w_format.text_left_format)

    table = create_table(values, parameters, w_format.number_format, w_format.wrap_format)
    rows_count = len(table['data'])
    worksheet.add_table(15, 0, rows_count + 15, len(parameters), table)

    worksheet.merge_range(
        rows_count + 17, 0, rows_count + 23, 3,
        'Расшифровка ошибок: \n'
        '(<) параметр < min\n'
        '(>) параметр > max\n'
        '(X) обрыв датчика\n'
        '(T) delta_t < min\n'
        '(R) перезапуск*)\n'
        '(C) коррекц.часов**)\n'
        '(#) электропитание\n',
        w_format.text_left_format
    )

    v_sup, v_ret, t_total = get_discharge(values=values)
    worksheet.merge_range('F13:G13', u'Расход подачи: ', w_format.text_right_format)
    worksheet.merge_range('H13:I13', f'{v_sup:.2f} м3/ч', w_format.number_format)
    worksheet.merge_range('J13:K13', u'Ду: 50 мм', w_format.text_left_format)
    worksheet.merge_range('F14:G14', u'Расход обратки: ', w_format.text_right_format)
    worksheet.merge_range('H14:I14', f'{v_ret:.2f} м3/ч', w_format.number_format)
    worksheet.merge_range('J14:K14', u'Ду: 25 мм', w_format.text_left_format)

    worksheet.merge_range(rows_count + 24, 0, rows_count + 24, 1, f'Tобщ = {t_total}')

    return worksheet


def carat_worksheet(worksheet: Worksheet, w_format, metering_point, device, date,
                    user, date_from=None, date_to=None, headers=None, report_type='DAILY'):
    default_parameters = [
        ('t1', 't1\n\u00B0C'),
        ('P1', 'P1\nкгс/см\u00B2'),
        ('M1', 'M1\nт'),
        ('t2', 't2\n\u00B0C'),
        ('P2', 'P2\nкгс/см\u00B2'),
        ('dp', 'dP\nкгс/см\u00B2'),
        ('v1', 'V1\nм\u00B3'),
        ('v2', 'V2\nм\u00B3'),
        ('M2', 'M2\nт'),
        ('Qo', 'Qот\nГкал'),
        ('dm', 'dM\nт'),
        ('tx', 'tx\n\u00B0C'),
        ('tg', 'tгвс\n\u00B0C'),
        ('Mg', 'Mгвс\nт'),
        ('tc', 'tцирк\n\u00B0C'),
        ('Mc', 'Mцирк\nт'),
        ('Mp', 'Mпотр\nт'),
        ('Qg', 'Qгвс\nГкал'),
        ('ВНР', 'ВНР\nч'),
        ('ВОС', 'ВОС\nч'),
        ('НС', 'НС'),
    ]
    parameters = get_parameters(default_parameters, headers)

    title = {
        'CURRENT': u'Отчет о текущих параметрах',
        'HOURLY': u'Отчет о часовых параметрах',
        'DAILY': u'Отчет о суточных параметрах',
        'MONTHLY': u'Отчет месячных параметрах',
    }

    values = metering_point.get('values')
    mp = metering_point.get('metering_point')
    report_date = mp.approved_from.strftime('%d.%m.%Y') if mp.approved_from else None

    worksheet.set_default_row(20)
    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:V', 7)
    worksheet.set_row(15, 30)
    worksheet.set_row(4, 30)

    worksheet.merge_range('A1:V3', get_title(title[report_type], date_from, date_to), w_format.head_format)

    worksheet.merge_range('A4:B4', u'Абонент: ', w_format.text_right_format)
    worksheet.merge_range('C4:E4', device.company_object.name, w_format.text_left_format)
    worksheet.merge_range('A5:B5', u'Адрес: ', w_format.text_right_format)
    worksheet.merge_range('C5:G5', device.company_object.address, w_format.address_format)
    worksheet.merge_range('A6:B6', u'Тепловычислитель Карат-307: ', w_format.text_right_format)
    worksheet.merge_range('C6:E6', '', w_format.text_left_format)
    worksheet.merge_range('A7:B7', u'Заводской номер: ', w_format.text_right_format)
    worksheet.merge_range('C7:E7', device.serial_number, w_format.text_left_format)
    worksheet.merge_range('I4:K4', u'Договор №: ', w_format.text_right_format)
    worksheet.merge_range('L4:M4', '', w_format.text_left_format)
    worksheet.merge_range('I5:K5', u'Тип расходомера: ', w_format.text_right_format)
    worksheet.merge_range('L5:M5', '', w_format.text_left_format)

    worksheet.merge_range('A8:O8', '')

    worksheet.merge_range('A9:B9', u'Договорные расходы:', w_format.text_right_format)
    worksheet.merge_range('A10:B10', u'М сет.воды =', w_format.text_right_format)
    worksheet.merge_range('C10:E10', '___т.сут', w_format.text_left_format)
    worksheet.merge_range('A11:B11', u'Мгвс =', w_format.text_right_format)
    worksheet.merge_range('C11:E11', '___т.сут', w_format.text_left_format)
    worksheet.merge_range('A12:B12', u'tхв: ', w_format.text_right_format)
    worksheet.merge_range('C12:E12', 'догов.', w_format.text_left_format)
    worksheet.merge_range('A13:B13', u'tхд =', w_format.text_right_format)
    worksheet.merge_range('C13:E13', '0.00 \u00B0C', w_format.text_left_format)
    worksheet.merge_range('I9:K9', u'Переделы измерений:', w_format.text_right_format)
    worksheet.merge_range('I10:K10', u'Gпод max:', w_format.text_right_format)
    worksheet.merge_range('L10:M10', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N10:O10', u'Gпод min:', w_format.text_right_format)
    worksheet.merge_range('P10:Q10', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('I11:K11', u'Gобр max:', w_format.text_right_format)
    worksheet.merge_range('L11:M11', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N11:O11', u'Gобр min:', w_format.text_right_format)
    worksheet.merge_range('P11:Q11', '___м3/ч', w_format.text_left_format)

    worksheet.merge_range('A14:B14', u'Дата формирования отчета: ', w_format.text_right_format)
    worksheet.merge_range('C14:E14', date, w_format.text_left_format)

    table = create_table(values, parameters, w_format.number_format, w_format.wrap_format)
    rows_count = len(table['data'])
    worksheet.add_table(15, 0, rows_count + 15, len(parameters), table)

    return worksheet


def vkt7_worksheet(worksheet: Worksheet, w_format, metering_point, device, date,
                   user, date_from=None, date_to=None, headers=None, report_type='DAILY'):
    default_parameters = [
        ('t1', 't1\n\u00B0C'),
        ('t2', 't2\n\u00B0C'),
        ('dt', 'dt\n\u00B0C'),
        ('v1', 'V1\nм\u00B3'),
        ('M1', 'M1\nт'),
        ('v2', 'V2\nм\u00B3'),
        ('M2', 'M2\nт'),
        ('v3', 'V3\nм\u00B3'),
        ('M3', 'M3\nт'),
        ('Mg', 'Mг\nт'),
        ('P1', 'P1\nкгс/см\u00B2'),
        ('P2', 'P2\nкгс/см\u00B2'),
        ('dp', 'dP\nкгс/см\u00B2'),
        ('Qo', 'Qот\nГкал'),
        ('Qg', 'Qгвс\nГкал'),
        ('ВНР', 'ВНР\nч'),
        ('ВОС', 'ВОС\nч'),
        ('НС', 'НС'),  # TODO непонятно что там в таблице
    ]
    parameters = get_parameters(default_parameters, headers)

    title = {
        'CURRENT': u'Отчет о текущих параметрах теплоснабжения',
        'HOURLY': u'Отчет о часовых параметрах теплоснабжения',
        'DAILY': u'Отчет о суточных параметрах теплоснабжения',
        'MONTHLY': u'Отчет месячных параметрах теплоснабжения',
    }

    values = metering_point.get('values')
    mp = metering_point.get('metering_point')
    report_date = mp.approved_from.strftime('%d.%m.%Y') if mp.approved_from else None

    worksheet.set_default_row(20)
    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:V', 7)
    worksheet.set_row(15, 30)
    worksheet.set_row(4, 30)

    worksheet.merge_range('A1:V3', get_title(title[report_type], date_from, date_to), w_format.head_format)

    worksheet.merge_range('A4:B4', u'Абонент: ', w_format.text_right_format)
    worksheet.merge_range('C4:E4', device.company_object.name, w_format.text_left_format)
    worksheet.merge_range('A5:B5', u'Адрес: ', w_format.text_right_format)
    worksheet.merge_range('C5:G5', device.company_object.address, w_format.address_format)
    worksheet.merge_range('A6:B6', u'Тепловычислитель:', w_format.text_right_format)
    worksheet.merge_range('C6:E6', 'ВКТ-7', w_format.text_left_format)
    worksheet.merge_range('A7:B7', u'Заводской номер: ', w_format.text_right_format)
    worksheet.merge_range('C7:E7', device.serial_number, w_format.text_left_format)
    worksheet.merge_range('I4:K4', u'Договор №: ', w_format.text_right_format)
    worksheet.merge_range('L4:M4', '', w_format.text_left_format)
    worksheet.merge_range('I5:K5', u'Тип расходомера: ', w_format.text_right_format)
    worksheet.merge_range('L5:M5', '', w_format.text_left_format)

    worksheet.merge_range('A8:O8', '')

    worksheet.merge_range('A9:B9', u'Договорные расходы:', w_format.text_right_format)
    worksheet.merge_range('A10:B10', u'М сет.воды =', w_format.text_right_format)
    worksheet.merge_range('C10:E10', '___т.сут', w_format.text_left_format)
    worksheet.merge_range('A11:B11', u'Мгвс =', w_format.text_right_format)
    worksheet.merge_range('C11:E11', '___т.сут', w_format.text_left_format)
    worksheet.merge_range('A12:B12', u'tхв: ', w_format.text_right_format)
    worksheet.merge_range('C12:E12', 'догов.', w_format.text_left_format)
    worksheet.merge_range('A13:B13', u'tхд =', w_format.text_right_format)
    worksheet.merge_range('C13:E13', '0.00 \u00B0C', w_format.text_left_format)
    worksheet.merge_range('I9:K9', u'Переделы измерений:', w_format.text_right_format)
    worksheet.merge_range('I10:K10', u'Gпод max:', w_format.text_right_format)
    worksheet.merge_range('L10:M10', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N10:O10', u'Gпод min:', w_format.text_right_format)
    worksheet.merge_range('P10:Q10', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('I11:K11', u'Gобр max:', w_format.text_right_format)
    worksheet.merge_range('L11:M11', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N11:O11', u'Gобр min:', w_format.text_right_format)
    worksheet.merge_range('P11:Q11', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('I12:K12', u'G3 max:', w_format.text_right_format)
    worksheet.merge_range('L12:M12', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N12:O12', u'G3 min:', w_format.text_right_format)
    worksheet.merge_range('P12:Q12', '___м3/ч', w_format.text_left_format)

    worksheet.merge_range('A14:B14', u'Дата формирования отчета: ', w_format.text_right_format)
    worksheet.merge_range('C14:E14', date, w_format.text_left_format)

    table = create_table(values, parameters, w_format.number_format, w_format.wrap_format)
    rows_count = len(table['data'])
    worksheet.add_table(15, 0, rows_count + 15, len(parameters), table)

    return worksheet


def tv7_worksheet(worksheet: Worksheet, w_format, metering_point, device, date,
                  user, date_from=None, date_to=None, headers=None, report_type='DAILY'):
    default_parameters = [
        ('t1', 't1 \u00B0C'),
        ('t2', 't2 \u00B0C'),
        ('dt', 'dt \u00B0C'),
        ('P1', 'P1 кгс/см\u00B2'),
        ('P2', 'P2 кгс/см\u00B2'),
        ('dp', 'dP кгс/см\u00B2'),
        ('v1', 'V1 м\u00B3'),
        ('v2', 'V2 м\u00B3'),
        ('M1', 'M1 т'),
        ('M2', 'M2 т'),
        ('dm', 'dM т'),
        ('tx', 'tx \u00B0C'),
        ('px', 'Px кгс/см\u00B2'),
        ('Qo', 'Qтв Гкал'),
        ('ВНР', 'ВНР ч'),
        ('ВОС', 'ВОС ч'),
        ('НС', 'НС'),
    ]
    parameters = get_parameters(default_parameters, headers)

    title = {
        'CURRENT': u'Отчет о текущих параметрах',
        'HOURLY': u'Отчет о часовых параметрах',
        'DAILY': u'Отчет о суточных параметрах',
        'MONTHLY': u'Отчет месячных параметрах',
    }

    values = metering_point.get('values')
    mp = metering_point.get('metering_point')
    report_date = mp.approved_from.strftime('%d.%m.%Y') if mp.approved_from else None

    worksheet.set_default_row(20)
    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:V', 10)

    worksheet.merge_range('A1:V3', get_title(title[report_type], date_from, date_to), w_format.head_format)

    worksheet.merge_range('A4:B4', u'Абонент: ', w_format.text_right_format)
    worksheet.merge_range('C4:E4', device.company_object.name, w_format.text_left_format)
    worksheet.merge_range('A5:B5', u'Адрес: ', w_format.text_right_format)
    worksheet.merge_range('C5:E5', device.company_object.address, w_format.text_left_format)
    worksheet.merge_range('A6:B6', u'Тепловычислитель Карат-307: ', w_format.text_right_format)
    worksheet.merge_range('C6:E6', '', w_format.text_left_format)
    worksheet.merge_range('A7:B7', u'Заводской номер: ', w_format.text_right_format)
    worksheet.merge_range('C7:E7', device.serial_number, w_format.text_left_format)
    worksheet.merge_range('J4:K4', u'Договор №: ', w_format.text_right_format)
    worksheet.merge_range('L4:M4', '', w_format.text_left_format)
    worksheet.merge_range('J5:K5', u'Тип расходомера: ', w_format.text_right_format)
    worksheet.merge_range('L5:M5', '', w_format.text_left_format)

    worksheet.merge_range('A8:O8', '')

    worksheet.merge_range('A9:B9', u'Договорные расходы:', w_format.text_right_format)
    worksheet.merge_range('A10:B10', u'М сет.воды =', w_format.text_right_format)
    worksheet.merge_range('C10:E10', '___т.сут', w_format.text_left_format)
    worksheet.merge_range('A11:B11', u'Мгвс =', w_format.text_right_format)
    worksheet.merge_range('C11:E11', '___т.сут', w_format.text_left_format)
    worksheet.merge_range('A12:B12', u'tхв: ', w_format.text_right_format)
    worksheet.merge_range('C12:E12', 'догов.', w_format.text_left_format)
    worksheet.merge_range('A13:B13', u'tхд =', w_format.text_right_format)
    worksheet.merge_range('C13:E13', '0.00 \u00B0C', w_format.text_left_format)
    worksheet.merge_range('J9:K9', u'Переделы измерений: ', w_format.text_right_format)
    worksheet.merge_range('J10:K10', u'Gпод max: ', w_format.text_right_format)
    worksheet.merge_range('L10:M10', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N10:O10', u'Gпод min: ', w_format.text_right_format)
    worksheet.merge_range('P10:Q10', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('J11:K11', u'Gобр max: ', w_format.text_right_format)
    worksheet.merge_range('L11:M11', '___м3/ч', w_format.text_left_format)
    worksheet.merge_range('N11:O11', u'Gобр min: ', w_format.text_right_format)
    worksheet.merge_range('P11:Q11', '___м3/ч', w_format.text_left_format)

    worksheet.merge_range('A14:B14', u'Дата формирования отчета: ', w_format.text_right_format)
    worksheet.merge_range('C14:E14', date, w_format.text_left_format)

    table = create_table(values, parameters, w_format.number_format, w_format.wrap_format)
    rows_count = len(table['data'])
    worksheet.add_table(15, 0, rows_count + 15, len(parameters), table)

    # FIXME итоговое потребление на начало и конец периода

    return worksheet


def tsrv043_worksheet(worksheet: Worksheet, w_format, metering_point, device, date,
                      user, date_from=None, date_to=None, headers=None, report_type='DAILY'):
    default_parameters = [
        ('q1', 'Qтс1, Гкал'),
        ('q2', 'Qтс2, Гкал'),
        ('q3', 'Qтс3, Гкал'),
        ('mt1', 'Mтс1, т'),
        ('mt2', 'Mтс2, т'),
        ('mt3', 'Mтс3, т'),
        ('m1', 'M1, т'),
        ('m2', 'M2, т'),
        ('m3', 'M3, т'),
        ('m4', 'M4, т'),
        ('v1', 'V1, м3'),
        ('v2', 'V2, м3'),
        ('v3', 'V3, м3'),
        ('v4', 'V4, м3'),
        ('p1', 'P1, МПа'),
        ('p2', 'P2, МПа'),
        ('dp', 'dP, МПа'),
        ('p3', 'P3, МПа'),
        ('p4', 'P4, МПа'),
        ('phv', 'Pхв, МПа'),
        ('t1', 't1, \u00B0C'),
        ('t2', 't2, \u00B0C'),
        ('t3', 't3, \u00B0C'),
        ('t4', 't4, \u00B0C'),
        ('t5', 't5, \u00B0C'),
        ('thv', 'tхв, \u00B0C'),
        ('Twork', 'Tраб, ч'),
        ('event', 'События'),
    ]
    parameters = get_parameters(default_parameters, headers)

    title = {
        'CURRENT': 'Ведомость учета текущих показаний параметров потребления тепловой энергии и теплоносителя',
        'HOURLY': 'Ведомость учета часовых значений параметров потребления тепловой энергии и теплоносителя',
        'DAILY': 'Ведомость учета суточных значений параметров потребления тепловой энергии и теплоносителя',
        'MONTHLY': 'Ведомость учета месячных значений параметров потребления тепловой энергии и теплоносителя',
    }

    values = metering_point.get('values')
    mp = metering_point.get('metering_point')
    report_date = mp.approved_from.strftime('%d.%m.%Y') if mp.approved_from else None

    worksheet.set_default_row(20)
    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:AC', 7)

    worksheet.merge_range('A1:AC3', get_title(title[report_type], date_from, date_to), w_format.head_format)

    worksheet.merge_range('A4:B4', 'Потребитель:', w_format.text_right_format)
    worksheet.merge_range('C4:K4', device.company_object.name, w_format.text_left_format)
    worksheet.merge_range('A5:B5', 'Адрес:', w_format.text_right_format)
    worksheet.merge_range('C5:K5', device.company_object.address, w_format.address_format)
    worksheet.merge_range('A6:B6', 'Договор:', w_format.text_right_format)
    worksheet.merge_range('C6:K6', '', w_format.text_left_format)

    worksheet.merge_range('M4:O4', 'Тип прибора:', w_format.text_right_format)
    worksheet.merge_range('P4:T4', 'ТСРВ-043', w_format.text_left_format)
    worksheet.merge_range('M5:O5', 'Номер прибора:', w_format.text_right_format)
    worksheet.merge_range('P5:T5', device.serial_number, w_format.text_left_format)

    worksheet.merge_range('W4:Y4', 'Наименьший расход теплоносителя Gmin:', w_format.text_right_format)
    worksheet.merge_range('Z4:AC4', '', w_format.text_left_format)
    worksheet.merge_range('W5:Y5', 'Наибольший расход теплоносителя Gmax:', w_format.text_right_format)
    worksheet.merge_range('Z5:AC5', '', w_format.text_left_format)

    worksheet.merge_range('A7:B7', u'Дата формирования отчета: ', w_format.text_right_format)
    worksheet.merge_range('C7:E7', date, w_format.text_left_format)

    table = create_table(values, parameters, w_format.number_format, w_format.wrap_format)
    rows_count = len(table['data'])
    worksheet.add_table(8, 0, rows_count + 8, len(parameters), table)

    # TODO Интеграторы и код ошибки


def sa94_worksheet(worksheet: Worksheet, w_format, metering_point, device, date,
                   user, date_from=None, date_to=None, headers=None, report_type='DAILY'):
    default_parameters = [
        ('Q1', 'Количество\nтепловой\nэнергии\nQ, Гкал'),
        ('M1', 'Под. труб. M1'),
        ('M2', 'Обр. труб. M2'),
        ('dm', 'Разность M1-M2'),
        ('V1', 'Под. труб. V1'),
        ('V2', 'Обр. труб. V2'),
        ('V3', 'V3'),
        ('T1', 't под.'),
        ('T2', 't обр.'),
        ('dt', 'dt'),
        ('p1', 'P под.'),
        ('p2', 'P обр.'),
        ('dp', 'dP'),
        ('Tн', 'Время\nнар-ки,\nТ нараб,\nчас'),
    ]
    parameters = get_parameters(default_parameters, headers)

    title = {
        'CURRENT': u'ОТЧЁТНАЯ ВЕДОМОСТЬ ЗА ПОТРЕБЛЁННОЕ ТЕПЛО И ТЕПЛОНОСИТЕЛЬ',
        'HOURLY': u'ОТЧЁТНАЯ ВЕДОМОСТЬ ЗА ПОТРЕБЛЁННОЕ ТЕПЛО И ТЕПЛОНОСИТЕЛЬ',
        'DAILY': u'ОТЧЁТНАЯ ВЕДОМОСТЬ ЗА ПОТРЕБЛЁННОЕ ТЕПЛО И ТЕПЛОНОСИТЕЛЬ',
        'MONTHLY': u'ОТЧЁТНАЯ ВЕДОМОСТЬ ЗА ПОТРЕБЛЁННОЕ ТЕПЛО И ТЕПЛОНОСИТЕЛЬ',
    }

    values = metering_point.get('values')
    mp = metering_point.get('metering_point')
    report_date = mp.approved_from.strftime('%d.%m.%Y') if mp.approved_from else None

    worksheet.set_default_row(20)
    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:O', 12)

    worksheet.merge_range('A1:O3', get_title(title[report_type], date_from, date_to), w_format.head_format)

    worksheet.merge_range('A4:B4', 'Номер абонента:', w_format.text_right_format)
    worksheet.merge_range('C4:I4', device.company_object.name, w_format.text_left_format)
    worksheet.merge_range('A5:B5', 'Адрес:', w_format.text_right_format)
    worksheet.merge_range('C5:I5', device.company_object.address, w_format.address_format)

    worksheet.merge_range('L4:M4', 'Тип прибора:', w_format.text_right_format)
    worksheet.merge_range('O4:O4', 'SA-94/2', w_format.text_left_format)
    worksheet.merge_range('L5:M5', 'Номер прибора:', w_format.text_right_format)
    worksheet.merge_range('N5:O5', device.serial_number, w_format.text_left_format)
    worksheet.merge_range('L6:M6', 'Конфигурация:', w_format.text_right_format)
    worksheet.merge_range('N6:O6', '200 - 11', w_format.text_left_format)

    worksheet.merge_range('A7:B7', 'Ду1:', w_format.text_right_format)
    worksheet.merge_range('C7:D7', '50', w_format.text_left_format)
    worksheet.merge_range('A8:B8', 'Ду2:', w_format.text_right_format)
    worksheet.merge_range('C8:D8', '50', w_format.text_left_format)
    worksheet.merge_range('E7:F7', 'G1наим:', w_format.text_right_format)
    worksheet.merge_range('G7:H7', '4.000', w_format.text_left_format)
    worksheet.merge_range('E8:F8', 'G2наим:', w_format.text_right_format)
    worksheet.merge_range('G8:H8', '4.000', w_format.text_left_format)
    worksheet.merge_range('I7:J7', 'G1наиб:', w_format.text_right_format)
    worksheet.merge_range('K7:K7', '25.0', w_format.text_left_format)
    worksheet.merge_range('I8:J8', 'G2наиб:', w_format.text_right_format)
    worksheet.merge_range('K8:K8', '25.0', w_format.text_left_format)

    worksheet.merge_range('A8:B8', u'Дата формирования отчета: ', w_format.text_right_format)
    worksheet.merge_range('C8:E8', date, w_format.text_left_format)

    table = create_table(values, parameters, w_format.number_format, w_format.wrap_format)
    rows_count = len(table['data'])
    worksheet.add_table(10, 0, rows_count + 10, len(parameters), table)

