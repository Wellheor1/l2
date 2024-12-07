import os.path
import re
from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile

from laboratory.settings import BASE_DIR


def add_schema_pdf(request_data):
    file_in_memory: InMemoryUploadedFile = request_data.get("file")
    file_content = file_in_memory.file.read()
    file_name = file_in_memory.name
    entity_id = request_data.get("entity_id")
    path = os.path.join(BASE_DIR, 'media', 'schemas-pdf')
    with open(f"{path}/service_id_{entity_id}__{file_name}", "wb") as file_on_disk:
        file_on_disk.write(file_content)
    return True


def get_schema_pdf_name(request_data):
    file_name = ""
    result = {}
    entity_id = request_data.get("entity_id")
    path = os.path.join(BASE_DIR, 'media', 'schemas-pdf')
    pattern = f'^service_id_{entity_id}__.*\.json$'
    file_list = os.listdir(path)
    for file_str in file_list:
        if re.search(pattern, file_str):
            file_name = file_str
    file_path = f"{path}/{file_name}"
    with open(file_path, "r") as file:
        print(file)
        created_at = os.stat(file_path).st_ctime
        created_at = datetime.fromtimestamp(created_at).strftime('%d.%m.%Y %H:%M')
        result["created_at"] = created_at
        result["pk"] = entity_id
        result["file_name"] = file_name
        result["file"] = file_path
    return result
