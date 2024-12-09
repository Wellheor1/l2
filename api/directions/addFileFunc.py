import os.path
import shutil
from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from directory.models import Researches
from laboratory.settings import MEDIA_URL, BASE_DIR


def add_schema_pdf(request_data):
    file_in_memory: InMemoryUploadedFile = request_data.get("file")
    entity_id = request_data.get("entity_id")
    current_service: Researches = Researches.objects.filter(pk=entity_id).first()
    if current_service:
        current_service.schema_pdf = file_in_memory
        current_service.save()
    return True


def get_schema_pdf(request_data):
    result = False
    entity_id = request_data.get("entity_id")
    service: Researches = Researches.objects.filter(pk=entity_id).first()
    if service and service.schema_pdf:
        created_at = os.stat(service.schema_pdf.path).st_ctime
        created_at = datetime.fromtimestamp(created_at).strftime('%d.%m.%Y %H:%M')
        result = {
            'pk': service.pk,
            'author': None,
            'createdAt': created_at,
            'file': service.schema_pdf.url if service.schema_pdf else None,
            'fileName': os.path.basename(service.schema_pdf.name) if service.schema_pdf else None,
        }
    return result


def delete_schema_pdf(request_data):
    entity_id = request_data.get("entity_id")
    service: Researches = Researches.objects.filter(pk=entity_id).first()
    if service and service.schema_pdf:
        service.schema_pdf.delete()
        shutil.rmtree(f"{BASE_DIR}/media/schemas-pdf/{entity_id}")
    return True
