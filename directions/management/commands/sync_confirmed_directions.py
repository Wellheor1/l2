from django.core.management.base import BaseCommand

from directions.models import Napravleniya


class Command(BaseCommand):
    help = "Синхронизировать оптимизированные поля подтверждений направлений"

    def handle(self, *args, **kwargs):
        d = Napravleniya.objects.all()
        total = d.count()
        cnt = 0
        n: Napravleniya
        for n in d:
            cnt += 1

            print(f"{cnt}/{total} синхронизируем {n.pk}...")  # noqa: T001
            n.sync_confirmed_fields()
            print(f"total_confirmed={n.total_confirmed} last_confirmed_at={n.last_confirmed_at}")  # noqa: T001
