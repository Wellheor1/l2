import uuid
from datetime import datetime
from django.db import models, transaction
from jsonfield import JSONField
from cash_registers import sql_func
from clients.models import Card
from directions.models import Napravleniya
from directory.models import Researches
from laboratory.utils import current_time
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


class CashRegister(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Наименование')
    ip_address = models.CharField(max_length=255, default="", verbose_name='IP адрес', help_text='192.168.10.10')
    port = models.CharField(max_length=5, default="", verbose_name='Порт', help_text='16333')
    login = models.CharField(max_length=255, default="", verbose_name='Логин', help_text='login')
    password = models.CharField(max_length=255, default="", verbose_name='Пароль', help_text='123456')
    hide = models.BooleanField(default=False, blank=True, verbose_name='Скрытие')
    address = models.CharField(max_length=128, blank=True, default='', verbose_name="Адрес")
    address_fias = models.CharField(max_length=128, blank=True, default=None, null=True, verbose_name="ФИАС Адрес")
    address_details = JSONField(blank=True, null=True, verbose_name="Детали адреса")
    department = models.ForeignKey(Podrazdeleniya, null=True, db_index=True, verbose_name="Подразделение", on_delete=models.SET_NULL)
    location = models.CharField(max_length=255, default="", verbose_name="Местоположение", help_text="2 этаж регистратура")

    class Meta:
        verbose_name = "Касса"
        verbose_name_plural = "Кассы"

    def __str__(self):
        return f"{self.title}"

    def json(self):
        return {
            "id": self.id,
            "label": self.title,
        }

    @staticmethod
    def get_cash_registers():
        result = [{"id": cash_register.id, "label": cash_register.title} for cash_register in sql_func.get_cash_registers()]
        return result

    @staticmethod
    def get_meta_data(cash_register_id=None, cash_register_obj=None):
        if cash_register_obj:
            cash_register_data = {"address": cash_register_obj.ip_address, "port": cash_register_obj.port, "login": cash_register_obj.login, "password": cash_register_obj.password}
        else:
            cash_register: CashRegister = CashRegister.objects.get(pk=cash_register_id)
            cash_register_data = {"address": cash_register.ip_address, "port": cash_register.port, "login": cash_register.login, "password": cash_register.password}
        return cash_register_data


class Shift(models.Model):
    cash_register = models.ForeignKey(CashRegister, verbose_name='Касса', help_text='Касса 1', null=True, on_delete=models.SET_NULL, db_index=True)
    open_at = models.DateTimeField(verbose_name='Время открытия', help_text='2024-07-28 16:00', null=True, blank=True, db_index=True)
    close_at = models.DateTimeField(verbose_name='Время закрытия', help_text='2024-07-28 23:00', null=True, blank=True, db_index=True)
    operator = models.ForeignKey(DoctorProfile, verbose_name='Оператор', help_text='Сидоров м.п', null=True, on_delete=models.SET_NULL, db_index=True)
    open_uuid = models.UUIDField(verbose_name='UUID открытия', help_text='abbfg-45fsd2', null=True, blank=True)
    close_uuid = models.UUIDField(verbose_name='UUID Закрытия', help_text='abbfg-45fsd2', null=True, blank=True)
    open_status = models.BooleanField(verbose_name='Статус открытия смены', default=False)
    close_status = models.BooleanField(verbose_name='Статус закрытия смены', default=False)

    class Meta:
        verbose_name = "Кассовая смена"
        verbose_name_plural = "Кассовые смены"

    def __str__(self):
        return f"{self.cash_register_id} - {self.open_at} - {self.close_at} - {self.operator}"

    @staticmethod
    def open_shift(uuid_data: str, cash_register_id: int, operator_id: int):
        new_shift: Shift = Shift(cash_register_id=cash_register_id, operator_id=operator_id, open_uuid=uuid_data)
        new_shift.save()
        return {"cash_register_id": new_shift.cash_register_id, "shift_id": new_shift.pk}

    def confirm_open_shift(self):
        self.open_status = True
        self.open_at = current_time()
        self.save()
        return True

    @staticmethod
    def close_shift(uuid_data: str, cash_register_id: int, operator_id: int):
        shift: Shift = Shift.objects.filter(cash_register_id=cash_register_id, operator_id=operator_id, open_status=True, close_status=False).last()
        shift.close_uuid = uuid_data
        shift.save()
        return True

    def confirm_close_shift(self):
        self.close_status = True
        self.close_at = current_time()
        self.save()
        return True

    @staticmethod
    def get_open_shift_by_operator(operator_id: int):
        shift: Shift = Shift.objects.filter(operator_id=operator_id, open_status=True, close_status=False).last()
        if shift:
            result = {"cash_register_id": shift.cash_register_id, "shift_id": shift.pk}
        else:
            result = {"cash_register_id": None, "shift_id": None}
        return result

    @staticmethod
    def check_shift(cash_register_id: int, doctor_profile_id: int):
        result_check = sql_func.check_shift(cash_register_id, doctor_profile_id)
        if len(result_check) == 0:
            result = {"ok": True, "message": ""}
        elif result_check[0].operator_id == doctor_profile_id:
            result = {"ok": False, "message": "У вас уже есть открытая смена"}
        else:
            result = {"ok": False, "message": "На этой кассе уже есть открытая смена"}
        return result

    @staticmethod
    def get_shift_job_data(doctor_profile_id: int, cash_register_id):
        operator: DoctorProfile = DoctorProfile.objects.get(pk=doctor_profile_id)
        operator_data = {"name": operator.get_full_fio(), "vatin": operator.inn}
        cash_register_data = CashRegister.get_meta_data(cash_register_id)
        uuid_data = str(uuid.uuid4())
        result = {"operator_data": operator_data, "cash_register_data": cash_register_data, "uuid_data": uuid_data}
        return result

    def get_shift_status(self):
        uuid_data = None
        if not self.open_status and self.open_uuid:
            status = "Открывается"
            uuid_data = self.open_uuid
        elif self.open_status and not self.close_uuid:
            status = "Открыта"
        else:
            status = "Закрывается"
            uuid_data = self.close_uuid
        return {"status": status, "uuid": uuid_data}

    @staticmethod
    def change_status(current_status, job_status, shift):
        if current_status == "Открывается":
            shift.confirm_open_shift()
            result = "Открыта"
        else:
            shift.confirm_close_shift()
            result = "Закрыта"
        return result

    @staticmethod
    def create_job_json(cash_register_data, uuid_data, operator, type_operations="openShift"):
        body = {"cashRegister": cash_register_data, "uuid": uuid_data, "job": [{"type": type_operations, "operator": operator}]}
        return body


class Cheque(models.Model):
    SELL = "sell"
    BUY = "buy"
    SELL_RETURN = "sell-return"
    BUY_RETURN = "buy-return"
    CASH_IN = "cash-in"
    CASH_OUT = "cash-out"
    TYPES = (
        (SELL, "Приход"),
        (BUY, "Расход"),
        (SELL_RETURN, "Возврат прихода"),
        (BUY_RETURN, "Возврат расхода"),
        (CASH_IN, "Внесение"),
        (CASH_OUT, "Выплата"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)
    shift = models.ForeignKey(Shift, verbose_name='Смена', help_text='1', null=True, on_delete=models.CASCADE, db_index=True)
    type = models.CharField(max_length=20, choices=TYPES, verbose_name='Тип операции', help_text='sell, buy и т.д', db_index=True)
    uuid = models.UUIDField(verbose_name='UUID', help_text='abbfg-45fsd2')
    status = models.BooleanField(verbose_name='Проведен', default=False, db_index=True)
    cancelled = models.BooleanField(verbose_name='Аннулирован', default=False, db_index=True)
    payment_cash = models.DecimalField(max_digits=10, verbose_name='Оплата наличными', default=0, decimal_places=2)
    received_cash = models.DecimalField(max_digits=10, verbose_name='Получено наличными', default=0, decimal_places=2)
    payment_electronic = models.DecimalField(max_digits=10, verbose_name='Оплата электронно', default=0, decimal_places=2)
    payment_at = models.DateTimeField(verbose_name='Время оплаты', help_text='2024-07-28 16:00', null=True, blank=True, db_index=True)
    card = models.ForeignKey(Card, verbose_name='Карта пациента/клиента', help_text='1', null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    row_data = JSONField(blank=True, null=True, verbose_name="Json чек-документ")

    class Meta:
        verbose_name = "Чек"
        verbose_name_plural = "Чеки"

    def __str__(self):
        return f"{self.type} - {self.shift} - {self.payment_at} - {self.card_id}"

    @staticmethod
    def create_payments(cash, received_cash, electronic):
        """
        Создание видов оплаты в чеке
        """
        result = []
        if cash:
            result.append({"type": "cash", "sum": received_cash})
        if electronic:
            result.append({"type": "electronically", "sum": electronic})
        return result

    @staticmethod
    def create_job_json(cash_register_data, uuid_data, type_operations, items, payments, total):
        """
        Создания тела запроса для middle server
        """
        body = {"cashRegister": cash_register_data, "uuid": uuid_data, "job": [{"type": type_operations, "items": items, "payments": payments, "total": total}]}
        return body

    @staticmethod
    def create_cheque(shift_id, type_operations, uuid_data, cash, received_cash, electronic, card_id, items):
        """
        Создание чека в базе
        """
        with transaction.atomic():
            new_cheque = Cheque(shift_id=shift_id, type=type_operations, uuid=uuid_data, payment_cash=cash, received_cash=received_cash, payment_electronic=electronic, card_id=card_id)
            new_cheque.save()
            for item in items:
                new_items = ChequeItems(cheque_id=new_cheque.pk, research_id=item["id"], coast=item["price"], discount=item["discount"], count=item["quantity"], amount=item["amount"])
                new_items.save()
            row_data = {
                "shift_id": shift_id,
                "type": type_operations,
                "uuid": uuid_data,
                "status": False,
                "cancelled": False,
                "payment_cash": cash,
                "received_cash": received_cash,
                "payment_electronic": electronic,
                "payment_at": None,
                "card_id": card_id,
                "items": items,
            }
            new_cheque.row_data = row_data
            new_cheque.save()
        return new_cheque.pk

    @staticmethod
    def get_patient_cheque(date_start, date_end, patient_card_pk):
        date_start_str = datetime.strftime(date_start, "%Y-%m-%d %H:%M")
        date_end_str = datetime.strftime(date_end, "%Y-%m-%d %H:%M")
        result = sql_func.get_patient_cheque(date_start_str, date_end_str, patient_card_pk)
        return result


class ChequeItems(models.Model):
    cheque = models.ForeignKey(Cheque, verbose_name='Чек', on_delete=models.CASCADE, db_index=True)
    research = models.ForeignKey(Researches, verbose_name='Услуга', null=True, on_delete=models.SET_NULL, db_index=True)
    coast = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за шт')
    discount = models.PositiveIntegerField(default=0, verbose_name='Скидка (%)')
    count = models.PositiveIntegerField(default=1, verbose_name='Количество')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма позиции')

    class Meta:
        verbose_name = "Элемент чека"
        verbose_name_plural = "Элементы чека"

    def __str__(self):
        return f"{self.cheque} - {self.research_id} - {self.count} - {self.amount}"

    @staticmethod
    def create_items(items):
        """
        Создание списка элементов чека
        """
        result = [
            {
                "id": item["id"],
                "type": "position",
                "name": item["title"],
                "price": float(item["discountedCoast"]),
                "discount": item["discountRelative"],
                "quantity": int(item["count"]),
                "amount": float(item["total"]),
                "tax": {"type": "none"},
                "paymentMethod": "fullPayment",
                "paymentObject": "service",
            }
            for item in items
        ]
        return result


class ChequeForDirection(models.Model):
    cheque = models.ForeignKey(Cheque, verbose_name='Чек', null=True, on_delete=models.SET_NULL, db_index=True)
    direction = models.ForeignKey(Napravleniya, verbose_name='Направления', null=True, on_delete=models.SET_NULL, db_index=True)

    class Meta:
        verbose_name = "Чек для направления"
        verbose_name_plural = "Чеки для направлений"

    def __str__(self):
        return f"{self.cheque} - {self.direction_id}"

    @staticmethod
    def create(cheque_id: int, directions_ids: list):
        for direction_id in directions_ids:
            cheque_for_direction = ChequeForDirection(cheque_id=cheque_id, direction_id=direction_id)
            cheque_for_direction.save()
