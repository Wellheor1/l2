from statistic.report import base_data
from statistic.statistic_func import initial_work_book, save_file_disk


def data_model_save_to_file(final_result, head_data, sheet_name, permanent_head_data, custom_fields):
    wb, ws = initial_work_book(sheet_name)
    ws = base_data.fill_default_base(ws, head_data)
    ws = base_data.fill_xls_model_statistic_data(ws, final_result, permanent_head_data, custom_fields)
    file_dir = save_file_disk(wb)
    return file_dir