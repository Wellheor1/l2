import json
from django.http import HttpResponse
import openpyxl

from api.reports import structure_sheet
from api.reports import sql_func
from api.reports import handle_func
from api.reports.sql_func import get_pair_direction_iss, get_simple_directions_for_hosp_stationar, get_field_results
from directory.models import StatisticPatternParamSet, ParaclinicInputField, Fractions, PatternParam, PatternParamTogether
from laboratory.settings import SEARCH_PAGE_STATISTIC_PARAMS
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def statistic_params_search(request):
    if request.method == "POST":
        data = json.loads(request.body)

        groups_user = [str(x) for x in request.user.groups.all()]
        response = HttpResponse("неверные параметры")

        param = data.get("param") or None
        research_id = data.get("researchId") or None
        if research_id:
            research_id = int(research_id)
        directions = data.get("directions") or None
        if not (param and research_id and directions):
            return response
        some_report = []
        for k, v in SEARCH_PAGE_STATISTIC_PARAMS.items():
            if k in groups_user:
                some_report.extend(v)
        if len(some_report) == 0:
            return response

        correct_group_param = False
        correct_group_research_id = False
        for v in some_report:
            correct_group_param = False
            correct_group_research_id = False
            for key, val in v.items():
                if key == "id" and val == param:
                    correct_group_param = True
                if key == "reserches_pk" and (research_id in val or val == "*"):
                    correct_group_research_id = True
                if correct_group_research_id and correct_group_param:
                    break
            if correct_group_research_id and correct_group_param:
                break

        if not (correct_group_param and correct_group_research_id):
            return response

        symbols = ("абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", "abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")  # Словарь для транслитерации
        tr = {ord(a): ord(b) for a, b in zip(*symbols)}  # Перевод словаря для транслита

        response = HttpResponse(content_type="application/ms-excel")
        wb = openpyxl.Workbook()
        wb.remove(wb.get_sheet_by_name("Sheet"))
        ws = wb.create_sheet("лист1")

        directions_data = tuple(list(set(directions)))
        if param == "1":
            result = sql_func.report_buh_gistology(directions_data)
            final_structure = handle_func.patologistology_buh(result)
            ws = structure_sheet.patologistology_buh_base(ws)
            ws = structure_sheet.patologistology_buh_data(ws, final_structure)

        title = "отчет"
        response["Content-Disposition"] = str.translate(f'attachment; filename="{title}.xlsx"', tr)
        wb.save(response)
        return response


@login_required
def xlsx_model(request):
    result_directions = None
    if request.method == "POST":
        data = json.loads(request.body)
        directions = data.get("directions")
        hosp_directions = data.get("hospDirections")
        id_model = data.get("idModel")
        sql_pair_direction_iss = {i.iss_id: i.direction_id for i in get_pair_direction_iss(tuple(hosp_directions))}

        sql_simple_directions = [i.direction_id for i in get_simple_directions_for_hosp_stationar(tuple(sql_pair_direction_iss.keys()))]
        directions.extend(sql_simple_directions)
        res_dir = set(directions)
        statistic_param_data = StatisticPatternParamSet.get_statistic_param(id_model)
        input_field_statistic_param = ParaclinicInputField.get_field_input_by_pattern_param(list(statistic_param_data.keys()))
        laboratory_fractions_statistic_param = Fractions.get_fraction_id_by_pattern_param(list(statistic_param_data.keys()))
        if len(laboratory_fractions_statistic_param) == 0:
            laboratory_fractions_statistic_param = [-1]
        result_directions = get_field_results(tuple(res_dir), tuple(input_field_statistic_param), tuple(laboratory_fractions_statistic_param))
        pattern_params = PatternParam.objects.filter(id__in=list(statistic_param_data.keys())).order_by("order").values("pk", "title")
        order_custom_field = {i.get('pk'): i.get('title') for i in pattern_params}
        print(order_custom_field)
        together_params = PatternParamTogether.get_together_param(list(order_custom_field.keys()))
        together_params_by_group = together_params.get("by_group")
        together_params_by_params = together_params.get("by_param")
        intermediate_structure_result = {}
        for i in result_directions:
            if not intermediate_structure_result.get(i.hospital_direction):
                intermediate_structure_result[i.hospital_direction] = {
                    "patient_fio": f"{i.patient_family} {i.patient_name} {i.patient_patronymic}",
                    "sex": i.sex,
                    "birthday": i.patient_birthday,
                    "age": i.patient_age,
                    "address": i.patient_fact_address if i.patient_fact_address else i.patient_main_address,
                    "protocol_directions": {}
                }
            if not intermediate_structure_result[i.hospital_direction]["protocol_directions"].get(i.protocol_direction_id):
                intermediate_structure_result[i.hospital_direction]["protocol_directions"][i.protocol_direction_id] = []
            intermediate_structure_result[i.hospital_direction]["protocol_directions"][i.protocol_direction_id].append(
                {
                    "input_static_param_id": i.input_static_param_id,
                    "field_title": i.field_title,
                    "input_value": i.input_value,
                    "fraction_static_param_id": i.fraction_static_param_id,
                    "fraction_value": i.fraction_value,
                    "time_confirm": i.time_confirm
                }
            )

        # print(result_directions)
        # print(intermediate_structure_result)
        fields = {"Случай": "", "Пациент": "", "Пол": "", "Дата рождения": "", "Возраст": "", "Адрес": ""}
        custom_fields = {v: "" for k, v in order_custom_field.items()}
        fields.update(custom_fields)
        print("custom_fields")
        print(custom_fields)
        final_result = []
        for k, v in intermediate_structure_result.items():
            print(k)
            print(v)
            print("--")
            intermediate_result = fields.copy()
            intermediate_result["Случай"] = k
            intermediate_result["Пациент"] = v.get('patient_fio')
            intermediate_result["Пол"] = v.get("sex")
            intermediate_result["Дата рождения"] = v.get("birthday")
            intermediate_result["Возраст"] = v.get("age")
            intermediate_result["Адрес"] = v.get("address")
            for direction_num, data_direction in v.get("protocol_directions").items():
                title_field = ""
                print("-----")
                for current_data in data_direction:
                    print(current_data)
                    group_id_block_param = None
                    if current_data.get("input_value"):
                        title_field = order_custom_field.get(current_data["input_static_param_id"])
                        group_id_block_param = together_params_by_params.get(current_data["input_static_param_id"])
                    elif current_data.get("fraction_value"):
                        title_field = order_custom_field.get(current_data["fraction_static_param_id"])
                        group_id_block_param = together_params_by_params.get(current_data["fraction_static_param_id"])
                    param_ids_in_group_block = together_params_by_group.get(group_id_block_param)
                    used_block_in_order_custom_field = [v for k, v in order_custom_field.items() if k in param_ids_in_group_block]
                    # проверить были ли значения полей заполнены уже БЛОКА-ВМЕСТЕ ранее
                    later_value = []
                    if len(used_block_in_order_custom_field) > 0:
                        later_value = [k for k in used_block_in_order_custom_field if intermediate_result.get(k)]
                    if len(later_value) > 0 or intermediate_result.get(title_field):
                        pass # сделай вторую строку для текущего параметра текущей истории
                    else:
                        pass # добавить в текущее поле

    return JsonResponse({"results": "file-xls-model", "link": "open-xls", "result": result_directions})
