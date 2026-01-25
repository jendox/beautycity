from __future__ import annotations

from django import template

register = template.Library()


@register.filter(name="rub")
def rub(value) -> str:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    formatted = format(number, ",").replace(",", " ")
    return f"{formatted} руб"
