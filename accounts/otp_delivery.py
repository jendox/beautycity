from config import settings


def deliver_otp(phone: str, code: str):
    if settings.SMS_DEBUG:
        print(f"phone: {phone}, otp:{code}")
        return

    # TODO: реализовать отправку СМС с OTP пользователю
    raise NotImplementedError()
