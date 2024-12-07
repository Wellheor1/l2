import os.path

from django.core.files.uploadedfile import InMemoryUploadedFile

from laboratory.settings import BASE_DIR


def add_schema_pdf(request_data):
    file_in_memory: InMemoryUploadedFile = request_data.get("file")
    file_content = file_in_memory.file.read()
    file_name = file_in_memory.name
    entity_id = request_data.get("entity_id")
    user = request_data.get("user")
    path = os.path.join(BASE_DIR, 'media', 'schemas-pdf')
    with open(f"{path}/service_id_{entity_id}__{file_name}", "wb") as file_on_disk:
        file_on_disk.write(file_content)
    return True
