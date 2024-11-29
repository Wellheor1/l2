from utils.db import namedtuplefetchall
from django.db import connection


def get_unique_method_instrumental_diagnostic():
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT distinct method
                from external_system_instrumentalresearchrefbook
                order by method DESC
        """,
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_nsi_code_fsidi(method):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                code_nsi, title, localization, area, code_nmu
                from external_system_instrumentalresearchrefbook
                where method=%(method)s
                order by title
        """,
            params={'method': method},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def cda_data_by_title(cda_title):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                id, 
                title
                from external_system_cdafields
                where title in %(cda_title)s
        """,
            params={'cda_title': cda_title},
        )
        rows = namedtuplefetchall(cursor)
    return rows

