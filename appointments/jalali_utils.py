import datetime

import jdatetime
from django.utils import timezone

PERSIAN_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

WEEKDAY_NAMES_FA = [
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنج‌شنبه",
    "جمعه",
]

_FA_DIGITS_TRANS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        if timezone.is_aware(value):
            try:
                value = timezone.localtime(value)
            except Exception:
                pass
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return None


def to_jalali_date(value):
    gregorian = _as_date(value)
    if gregorian is None:
        return None
    try:
        return jdatetime.date.fromgregorian(date=gregorian)
    except Exception:
        return None


def jalali_date_str(value):
    jd = to_jalali_date(value)
    if jd is None:
        return "-"
    return f"{jd.year}/{jd.month:02d}/{jd.day:02d}"


def jalali_full_str(value):
    gregorian = _as_date(value)
    jd = to_jalali_date(gregorian)
    if gregorian is None or jd is None:
        return "-"
    model_weekday = (gregorian.weekday() + 2) % 7
    weekday_name = WEEKDAY_NAMES_FA[model_weekday]
    month_name = PERSIAN_MONTHS[jd.month - 1]
    return f"{weekday_name} {jd.day} {month_name} {jd.year}"


def jalali_datetime_str(value):
    if isinstance(value, datetime.datetime):
        dt = value
        if timezone.is_aware(dt):
            try:
                dt = timezone.localtime(dt)
            except Exception:
                pass
        date_part = jalali_date_str(dt.date())
        if date_part == "-":
            return "-"
        return f"{date_part} {dt.hour:02d}:{dt.minute:02d}"
    return jalali_date_str(value)


def fa_digits(value):
    if value is None:
        return "-"
    return str(value).translate(_FA_DIGITS_TRANS)