import datetime
import re

import simplejson as json
from django.core import serializers
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from users.models import DoctorProfile
from . import models as Clients


def ignore_exception(IgnoreException=Exception, DefaultVal=None):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """

    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal

        return _dec

    return dec


def ajax_search_old(request):
    """ Поиск пациентов """
    objects = []
    if request.method == "GET" and request.GET['query'] and request.GET[
        'type']:  # Проверка типа запроса и наличия полей
        type = request.GET['type']
        query = request.GET['query'].strip()
        p = re.compile(r'[а-я]{3}[0-9]{8}',
                       re.IGNORECASE)  # Регулярное выражение для определения запроса вида иии10121999
        p2 = re.compile(
            r'([А-я]{2,}) ([А-я]{2,}) ([А-я]*) ([0-9]{2}.[0-9]{2}.[0-9]{4})')  # Регулярное выражение для определения запроса вида Иванов Иван Иванович 10.12.1999
        p3 = re.compile(r'[0-9]{1,10}')  # Регулярное выражение для определения запроса по номеру карты
        if re.search(p, query.lower()):  # Если это краткий запрос
            initials = query[0:3]
            btday = query[3:5] + "." + query[5:7] + "." + query[7:11] + " 0:00:00"
            if type == "all":
                objects = Clients.Importedclients.objects.filter(initials=initials, birthday=btday)[0:10]
            else:
                objects = Clients.Importedclients.objects.filter(initials=initials, birthday=btday, type=type)[0:10]
        elif re.search(p2, query):  # Если это полный запрос
            split = str(query).split()
            btday = split[3] + " 0:00:00"
            if type == "all":  # Проверка типа базы, all - поиск по Поликлиннике и по Стационару
                objects = Clients.Importedclients.objects.filter(family=split[0], name=split[1], twoname=split[2],
                                                                 birthday=btday)[0:10]
            else:
                objects = Clients.Importedclients.objects.filter(family=split[0], name=split[1], twoname=split[2],
                                                                 birthday=btday, type=type)[0:10]
        elif re.search(p3, query):  # Если это запрос номер карты
            try:
                objects = Clients.Importedclients.objects.filter(num=int(query), type=type)[0:10]
            except ValueError:
                pass
    return HttpResponse(serializers.serialize('json', objects), content_type="application/json")  # Создание JSON


from rmis_integration.client import Client


def ajax_search(request):
    """ Поиск пациентов """
    objects = []
    data = []
    if request.method == "GET" and request.GET['query'] and request.GET[
        'type']:  # Проверка типа запроса и наличия полей
        type = request.GET['type']
        card_type = Clients.CardBase.objects.get(pk=type)
        query = request.GET['query'].strip()
        p = re.compile(r'[а-я]{3}[0-9]{8}',
                       re.IGNORECASE)  # Регулярное выражение для определения запроса вида иии10121999
        p2 = re.compile(
            r'([А-я]{2,})( ([А-я]{2,})( ([А-я]*)( ([0-9]{2}.[0-9]{2}.[0-9]{4}))?)?)?')  # Регулярное выражение для определения запроса вида Иванов Иван Иванович 10.12.1999
        p3 = re.compile(r'[0-9]{1,15}')  # Регулярное выражение для определения запроса по номеру карты
        if re.search(p, query.lower()):  # Если это краткий запрос
            initials = query[0:3].upper()
            btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
            objects = Clients.Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1],
                                                        patronymic__startswith=initials[2], birthday=btday, card__base=card_type)
            if card_type.is_rmis and len(objects) == 0:
                c = Client()
                objects = c.patients.import_individual_to_base({"surname": query[0] + "%", "name": query[1] + "%", "patrName": query[2] + "%", "birthDate": btday}, fio=True)
        elif re.search(p2, query):  # Если это полный запрос
            split = str(query).split()
            f = n = p = btday = ""
            f = split[0]
            rmis_req = {"surname": f+"%"}
            if len(split) > 1:
                n = split[1]
                rmis_req["name"] = n+"%"
            if len(split) > 2:
                p = split[2]
                rmis_req["patrName"] = p+"%"
            if len(split) > 3:
                btday = split[3].split(".")
                btday = btday[2] + "-" + btday[1] + "-" + btday[0]
                rmis_req["birthDate"] = btday
            objects = Clients.Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                        patronymic__istartswith=p, card__base=card_type)[:10]
            if len(split) > 3:
                objects = objects.filter(birthday=btday)

            if card_type.is_rmis and (len(objects) == 0 or (len(split) < 4 and len(objects) < 10)):
                c = Client()
                objects = list(objects)
                objects += c.patients.import_individual_to_base(rmis_req, fio=True, limit=10-len(objects))

        if (re.search(p3, query) or card_type.is_rmis) and len(list(objects)) == 0:  # Если это запрос номер карты
            try:
                objects = Clients.Individual.objects.filter(card__number=query.upper(), card__is_archive=False,
                                                            card__base=card_type)
            except ValueError:
                pass
            if card_type.is_rmis and len(objects) == 0 and len(query) == 16:
                c = Client()
                objects = c.patients.import_individual_to_base(query)

        '''
        c = Client()
        for i in objects:
            c.patients.get_rmis_id_for_individual(i, True)'''

        for row in Clients.Card.objects.filter(base=card_type, individual__in=objects, is_archive=False).distinct():
            data.append({"type_title": card_type.title,
                         "num": row.number,
                         "family": row.individual.family,
                         "name": row.individual.name,
                         "twoname": row.individual.patronymic,
                         "birthday": row.individual.bd(),
                         "sex": row.individual.sex,
                         "pk": row.pk})
    return HttpResponse(json.dumps(data), content_type="application/json")  # Создание JSON


def get_db(request):
    key = request.GET["key"]
    code = request.GET["code"]
    data = []
    for x in Clients.Card.objects.filter(base__short_title=code, is_archive=False).prefetch_related():
        doc = x.individual.document_set.filter(
            document_type=Clients.DocumentType.objects.filter(title="Полис ОМС").first())
        data.append({
            "Family": x.individual.family,
            "Name": x.individual.name,
            "Twoname": x.individual.patronymic,
            "Sex": x.individual.sex,
            "Bday": "{:%d.%m.%Y}".format(x.individual.birthday),
            "Number": x.number,
            "Polisser": "" if not doc.exists() else doc.first().serial,
            "Polisnum": "" if not doc.exists() else doc.first().number
        })
    return HttpResponse(json.dumps(data), content_type="application/json")


@csrf_exempt
def receive_db(request):
    key = request.POST["key"]
    data = request.POST["data"]
    code = request.POST["code"]
    base = Clients.CardBase.objects.filter(short_title=code).first()
    d = json.loads(data)
    c = "OK"

    api_user = DoctorProfile.objects.filter(user__username="api").first()
    bulk_polises = []
    bulk_cards = []

    def fix(s: str):
        return s.strip().title()
    from rmis_integration.client import Client
    c = Client()
    for x in d:
        individual = Clients.Individual.objects.filter(family=x["Family"], name=x["Name"],
                                                       patronymic=x["Twoname"],
                                                       birthday=datetime.datetime.strptime(x["Bday"],
                                                                                           "%d.%m.%Y")).order_by("-pk")
        if not individual.exists():
            polis = Clients.Document.objects.filter(
                document_type=Clients.DocumentType.objects.filter(title="Полис ОМС").first(), serial=x["Polisser"],
                number=x["Polisnum"])
            if polis.exists():
                polis = polis[0]
                polis.individual.family = fix(x["Family"])
                polis.individual.name = fix(x["Name"])
                polis.individual.patronymic = fix(x["Twoname"]),
                polis.individual.birthday = datetime.datetime.strptime(x["Bday"], "%d.%m.%Y"),
                polis.individual.sex = x["Sex"].lower().strip()
                polis.individual.save()
            else:
                individual = Clients.Individual(family=fix(x["Family"]),
                                                name=fix(x["Name"]),
                                                patronymic=fix(x["Twoname"]),
                                                birthday=datetime.datetime.strptime(x["Bday"],
                                                                                    "%d.%m.%Y"),
                                                sex=x["Sex"])
                individual.save()
        else:
            individual = individual[0]
            if individual.sex != x["Sex"]:
                individual.sex = x["Sex"]
                individual.save()
        if x["Polisser"] != "" or x["Polisnum"] != "":
            polis = Clients.Document.objects.filter(
                document_type=Clients.DocumentType.objects.filter(title="Полис ОМС").first(), serial=x["Polisser"],
                number=x["Polisnum"], individual=individual).order_by("-pk")
            if not polis.exists():
                bulk_polises.append(Clients.Document(
                    document_type=Clients.DocumentType.objects.filter(title="Полис ОМС").first(), serial=x["Polisser"],
                    number=x["Polisnum"], individual=individual))
        c.patients.get_rmis_id_for_individual(individual, True)
        cards = Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False).exclude(
            individual=individual)
        cards.update(is_archive=True)
        cards.filter(napravleniya__isnull=True).delete()
        if not Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False).exists():
            bulk_cards.append(Clients.Card(number=x["Number"], base=base, individual=individual, is_archive=False))
    if len(bulk_polises) != 0:
        Clients.Document.objects.bulk_create(bulk_polises)
    if len(bulk_cards) != 0:
        Clients.Card.objects.bulk_create(bulk_cards)
    return HttpResponse("OK", content_type="text/plain")
