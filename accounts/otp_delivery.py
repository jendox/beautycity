from django.conf import settings


def deliver_otp(phone: str, code: str):
    if settings.DJANGO_SMS_DEBUG:
        print(f"phone: {phone}, otp:{code}")

    # TODO: реализовать отправку СМС с OTP пользователю
    raise NotImplementedError()
