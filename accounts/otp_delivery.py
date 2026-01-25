import logging

import requests

from config import settings


def deliver_otp(phone: str, code: str):
    if settings.SMS_DEBUG:
        logging.info(f"phone: {phone}, otp:{code}")
        return

    requests.post(
        url=f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        data={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": f"PHONE: {phone}\nOTP: <code>{code}</code>",
            "parse_mode": "HTML",
        },
    )
