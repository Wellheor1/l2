import uuid
from cash_registers.models import CashRegister, Shift
import cash_registers.req as cash_req
from users.models import DoctorProfile


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def get_cash_register_data(cash_register_id):
    cash_register: CashRegister = CashRegister.objects.get(pk=cash_register_id)
    cash_register_data = {"address": cash_register.ip_address, "port": cash_register.port, "login": cash_register.login, "password": cash_register.password}
    return cash_register_data


def get_shift_job_data(doctor_profile_id: int, cash_register_id):
    operator: DoctorProfile = DoctorProfile.objects.get(pk=doctor_profile_id)
    operator_data = {"name": operator.get_full_fio(), "vatin": operator.inn}
    cash_register_data = get_cash_register_data(cash_register_id)
    uuid_data = str(uuid.uuid4())
    return operator_data, cash_register_data, uuid_data


def open_shift(cash_register_id: int, doctor_profile_id: int):
    check_shift = Shift.check_shift(cash_register_id, doctor_profile_id)
    if not check_shift["ok"]:
        return check_shift
    operator_data, cash_register_data, uuid_data = get_shift_job_data(doctor_profile_id, cash_register_id)
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if not check_cash_register["ok"]:
        return check_cash_register
    job_result = cash_req.open_shift(uuid_data, cash_register_data, operator_data)
    if not job_result["ok"]:
        return job_result
    Shift.open_shift(str(uuid_data), cash_register_id, doctor_profile_id)
    return {"ok": True, "message": ""}


def close_shift(cash_register_id: int, doctor_profile_id: int):
    operator_data, cash_register_data, uuid_data = get_shift_job_data(doctor_profile_id, cash_register_id)
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if not check_cash_register["ok"]:
        return check_cash_register
    job_result = cash_req.close_shift(uuid_data, cash_register_data, operator_data)
    if not job_result["ok"]:
        return job_result
    result = Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
    return {"ok": result, "message": ""}


def get_shift_data(doctor_profile_id: int):
    shift: Shift = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).select_related('cash_register').last()
    uuid_data = None
    status = None
    if not shift:
        print('мы тут что-ли?')
        return {"ok": False, "data": shift}
    if not shift.open_status and shift.open_uuid:
        status = 0
        uuid_data = shift.open_uuid
    elif shift.open_status and not shift.close_uuid:
        status = 1
    elif shift.open_status and shift.close_uuid:
        status = 2
        uuid_data = shift.close_uuid
    if not uuid_data:
        data = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "status": status}
        return {"ok": True, "data": data}

    cash_register_data = get_cash_register_data(shift.cash_register_id)
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    print(status)
    if not check_cash_register["ok"]:
        return check_cash_register
    job_result = cash_req.get_job_status(str(uuid_data), cash_register_data)
    if not job_result["ok"]:
        return {"ok": False, "message": "Ошибка проверки задания"}
    job_status = job_result["data"]["results"][0]
    print(job_status)
    print(status)
    if job_status["status"] == "ready" and status == 0:
        confirm_open = Shift.confirm_open_shift(shift.pk)
        status = 1
    elif job_status["status"] == "ready" and status == 2:
        confirm_close = Shift.confirm_close_shift(shift.pk)
        status = -1
    data = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "status": status}
    return {"ok": True, "data": data}
