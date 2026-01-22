import phonenumbers
from phonenumber_field.phonenumber import PhoneNumber

from config import settings


def normalize_phone(raw_phone: str) -> str:
    raw_phone = (raw_phone or "").strip()
    if not raw_phone:
        raise ValueError("empty_phone")
    default_region = getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)
    try:
        number = phonenumbers.parse(raw_phone, default_region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("parse_error") from exc

    if not phonenumbers.is_possible_number(number) or not phonenumbers.is_valid_number(number):
        raise ValueError("invalid_phone")

    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def phone_to_user_field(phone_e164: str) -> str:
    return PhoneNumber.from_string(phone_e164)
