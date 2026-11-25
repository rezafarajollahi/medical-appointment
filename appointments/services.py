from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from doctors.models import DoctorProfile

from .models import Appointment, AppointmentNotification

BOOKING_WINDOW_DAYS = 14

WEEKDAY_NAMES = [
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنج‌شنبه",
    "جمعه",
]


class BookingError(Exception):
    pass


def local_now():
    return timezone.localtime().replace(tzinfo=None)


def model_weekday(day):
    return (day.weekday() + 2) % 7


def _overlaps(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def get_free_slots(doctor, start_date=None, days=BOOKING_WINDOW_DAYS):
    if doctor.visit_duration <= 0:
        return []

    now = local_now()
    start_date = start_date or now.date()
    end_date = start_date + timedelta(days=days - 1)
    duration = timedelta(minutes=doctor.visit_duration)

    availabilities = list(
        doctor.availabilities.filter(is_active=True).order_by("start_time")
    )
    times_off = list(doctor.times_off.filter(date__range=(start_date, end_date)))
    booked = list(
        Appointment.objects.filter(
            doctor=doctor,
            appointment_date__range=(start_date, end_date),
        )
        .exclude(status=Appointment.Status.CANCELLED)
        .values_list("appointment_date", "start_time", "end_time")
    )

    result = []

    for offset in range(days):
        day = start_date + timedelta(days=offset)
        weekday = model_weekday(day)

        day_off = [item for item in times_off if item.date == day]
        if any(item.start_time is None for item in day_off):
            continue

        day_booked = [(start, end) for date, start, end in booked if date == day]
        slots = []

        for availability in availabilities:
            if availability.weekday != weekday:
                continue
            if availability.valid_from and day < availability.valid_from:
                continue
            if availability.valid_to and day > availability.valid_to:
                continue

            current = datetime.combine(day, availability.start_time)
            limit = datetime.combine(day, availability.end_time)

            while current + duration <= limit:
                slot_start = current.time()
                slot_end = (current + duration).time()

                is_future = current > now
                is_off = any(
                    _overlaps(slot_start, slot_end, item.start_time, item.end_time)
                    for item in day_off
                )
                is_booked = any(
                    _overlaps(slot_start, slot_end, start, end)
                    for start, end in day_booked
                )

                if is_future and not is_off and not is_booked:
                    slots.append(
                        {
                            "start": slot_start,
                            "end": slot_end,
                            "url_time": slot_start.strftime("%H-%M"),
                        }
                    )

                current += duration

        if slots:
            result.append(
                {
                    "date": day,
                    "weekday_name": WEEKDAY_NAMES[weekday],
                    "url_date": day.isoformat(),
                    "slots": slots,
                }
            )

    return result


def is_slot_free(doctor, day, start_time):
    today = local_now().date()
    last_day = today + timedelta(days=BOOKING_WINDOW_DAYS - 1)

    if day < today or day > last_day:
        return False

    days = get_free_slots(doctor, start_date=day, days=1)
    return any(
        slot["start"] == start_time for item in days for slot in item["slots"]
    )


@transaction.atomic
def book_appointment(patient, doctor, day, start_time, description=""):
    doctor = DoctorProfile.objects.select_for_update().get(pk=doctor.pk)

    if not (doctor.is_active and doctor.is_verified):
        raise BookingError("این پزشک در حال حاضر قابل نوبت‌دهی نیست.")

    if not is_slot_free(doctor, day, start_time):
        raise BookingError(
            "این زمان دیگر آزاد نیست. لطفاً زمان دیگری انتخاب کنید."
        )

    end_time = (
        datetime.combine(day, start_time)
        + timedelta(minutes=doctor.visit_duration)
    ).time()

    has_conflict = (
        Appointment.objects.filter(
            patient=patient,
            appointment_date=day,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        .exclude(status=Appointment.Status.CANCELLED)
        .exists()
    )
    if has_conflict:
        raise BookingError("شما در این زمان نوبت دیگری دارید.")

    appointment = Appointment(
        patient=patient,
        doctor=doctor,
        appointment_date=day,
        start_time=start_time,
        end_time=end_time,
        status=Appointment.Status.CONFIRMED,
        patient_description=description,
    )

    try:
        appointment.full_clean()
    except ValidationError as error:
        raise BookingError(" ".join(error.messages))

    appointment.save()

    AppointmentNotification.objects.create(
        appointment=appointment,
        recipient=patient,
        notification_type=AppointmentNotification.NotificationType.CONFIRMATION,
    )

    return appointment


def has_started(appointment):
    starts_at = datetime.combine(
        appointment.appointment_date, appointment.start_time
    )
    return starts_at <= local_now()


def can_cancel(appointment):
    cancellable = (
        Appointment.Status.PENDING,
        Appointment.Status.CONFIRMED,
    )
    return appointment.status in cancellable and not has_started(appointment)


@transaction.atomic
def cancel_appointment(appointment, reason=""):
    if not can_cancel(appointment):
        raise BookingError("این نوبت قابل لغو نیست.")

    appointment.status = Appointment.Status.CANCELLED
    appointment.cancellation_reason = reason
    appointment.cancelled_at = timezone.now()
    appointment.save()

    AppointmentNotification.objects.create(
        appointment=appointment,
        recipient=appointment.patient,
        notification_type=AppointmentNotification.NotificationType.CANCELLATION,
    )

    return appointment