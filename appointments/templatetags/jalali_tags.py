from django import template

from appointments.jalali_utils import (
    fa_digits as _fa_digits,
    jalali_date_str as _jalali_date_str,
    jalali_datetime_str as _jalali_datetime_str,
    jalali_full_str as _jalali_full_str,
)

register = template.Library()


@register.filter(name="jalali_date")
def jalali_date_filter(value):
    return _jalali_date_str(value)


@register.filter(name="jalali_full")
def jalali_full_filter(value):
    return _jalali_full_str(value)


@register.filter(name="jalali_datetime")
def jalali_datetime_filter(value):
    return _jalali_datetime_str(value)


@register.filter(name="fa_digits")
def fa_digits_filter(value):
    return _fa_digits(value)