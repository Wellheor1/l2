import os.path
import re
import tempfile
from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile

from laboratory.settings import BASE_DIR, MEDIA_URL


def add_schema_pdf(request_data):
    file_in_memory: InMemoryUploadedFile = request_data.get("file")
    file_content = file_in_memory.file.read()
    file_name = file_in_memory.name
    entity_id = request_data.get("entity_id")
    path = os.path.join(BASE_DIR, 'media', 'schemas-pdf', str(entity_id))
    if not os.path.exists(path):
        os.makedirs(path)
    if len(os.listdir(path)) > 1:
        return False
    with open(f"{path}/{file_name}", "wb") as file_on_disk:
        file_on_disk.write(file_content)
    return True


def get_schema_pdf(request_data):
    file_name = None
    result = False
    entity_id = request_data.get("entity_id")
    path = os.path.join(BASE_DIR, 'media', 'schemas-pdf', str(entity_id))
    if os.path.exists(path):
        file_list = os.listdir(path)
        for file in file_list:
            file_name = file
    if file_name:
        file_path = f"{path}/{file_name}"
        created_at = os.stat(file_path).st_ctime
        created_at = datetime.fromtimestamp(created_at).strftime('%d.%m.%Y %H:%M')
        result = {
            "created_at": created_at,
            "file_name": file_name,
            "file": f"{MEDIA_URL}schemas-pdf/{entity_id}/{file_name}",
            "pk": entity_id,
        }
    return result


def delete_schema_pdf(request_data):
    file_name = request_data.get("file_name")
    entity_id = request_data.get("entity_id")
    path = os.path.join(BASE_DIR, 'media', 'schemas-pdf', str(entity_id))
    file_path = f"{path}/{file_name}"
    if os.path.exists(file_path):
        os.remove(file_path)
    return True
