from datetime import datetime

from django.contrib import messages
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import doctor_profile_required, patient_required
from doctors.models import DoctorProfile

from .forms import BookingForm, CancelForm, ReviewForm
from .models import Appointment, Review
from .jalali_utils import fa_digits, jalali_full_str
from .services import (
    BookingError,
    book_appointment,
    can_cancel,
    cancel_appointment,
    has_started,
    is_slot_free,
)
from .services import (
    WEEKDAY_NAMES,
    BookingError,
    book_appointment,
    can_cancel,
    cancel_appointment,
    has_started,
    is_slot_free,
    model_weekday,
)


@patient_required
def book(request, doctor_id, date_str, time_str):
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("user", "specialty"),
        pk=doctor_id,
        is_active=True,
        is_verified=True,
    )

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(time_str, "%H-%M").time()
    except ValueError:
        raise Http404("تاریخ یا ساعت نامعتبر است.")

    form = BookingForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            book_appointment(
                patient=request.user,
                doctor=doctor,
                day=day,
                start_time=start_time,
                description=form.cleaned_data["patient_description"],
            )
        except BookingError as error:
            messages.error(request, str(error))
            return redirect("doctors:detail", pk=doctor.pk)
        except IntegrityError:
            messages.error(request, "این زمان لحظاتی پیش توسط فرد دیگری رزرو شد.")
            return redirect("doctors:detail", pk=doctor.pk)

        messages.success(request, "نوبت شما با موفقیت ثبت شد.")
        return redirect("appointments:my_appointments")

    if not is_slot_free(doctor, day, start_time):
        messages.error(request, "این زمان دیگر آزاد نیست.")
        return redirect("doctors:detail", pk=doctor.pk)

    description = (
        f"{doctor} ({doctor.specialty}) - "
        f"{fa_digits(jalali_full_str(day))} "
        f"ساعت {fa_digits(start_time.strftime('%H:%M'))}"
    )

    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "تأیید دریافت نوبت",
            "description": description,
            "submit_label": "ثبت نوبت",
        },
    )


@patient_required
def my_appointments(request):
    appointments = list(
        Appointment.objects.filter(patient=request.user).select_related(
            "doctor__user",
            "doctor__specialty",
            "review",
        )
    )

    for appointment in appointments:
        appointment.can_cancel = can_cancel(appointment)
        appointment.can_review = (
            appointment.status == Appointment.Status.COMPLETED
            and not hasattr(appointment, "review")
        )

    return render(
        request,
        "appointments/patient_appointments.html",
        {"appointments": appointments},
    )


@patient_required
def cancel(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("doctor__user"),
        pk=pk,
        patient=request.user,
    )

    if not can_cancel(appointment):
        messages.error(request, "این نوبت قابل لغو نیست.")
        return redirect("appointments:my_appointments")

    form = CancelForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            cancel_appointment(appointment, form.cleaned_data["reason"])
            messages.success(request, "نوبت شما لغو شد.")
        except BookingError as error:
            messages.error(request, str(error))
        return redirect("appointments:my_appointments")

    description = (
        f"لغو نوبت {appointment.doctor} در تاریخ "
        f"{fa_digits(jalali_full_str(appointment.appointment_date))} "
        f"ساعت {fa_digits(appointment.start_time.strftime('%H:%M'))}"
    )

    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "لغو نوبت",
            "description": description,
            "submit_label": "تأیید لغو",
        },
    )


@patient_required
def review_create(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("doctor__user"),
        pk=pk,
        patient=request.user,
    )

    if appointment.status != Appointment.Status.COMPLETED:
        messages.error(request, "فقط برای نوبت تکمیل‌شده می‌توان نظر ثبت کرد.")
        return redirect("appointments:my_appointments")

    if Review.objects.filter(appointment=appointment).exists():
        messages.error(request, "برای این نوبت قبلاً نظر ثبت شده است.")
        return redirect("appointments:my_appointments")

    form = ReviewForm(
        request.POST or None,
        instance=Review(appointment=appointment),
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "نظر شما ثبت شد.")
        return redirect("appointments:my_appointments")

    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": f"ثبت نظر برای {appointment.doctor}",
            "submit_label": "ثبت نظر",
        },
    )


@doctor_profile_required
def doctor_appointments(request):
    scope = request.GET.get("scope", "upcoming")
    today = timezone.localdate()
    appointments = request.doctor.appointments.select_related("patient")

    if scope == "today":
        appointments = appointments.filter(appointment_date=today).order_by(
            "start_time"
        )
    elif scope == "past":
        appointments = appointments.filter(appointment_date__lt=today)
    elif scope == "cancelled":
        appointments = appointments.filter(status=Appointment.Status.CANCELLED)
    else:
        scope = "upcoming"
        appointments = (
            appointments.filter(appointment_date__gte=today)
            .exclude(status=Appointment.Status.CANCELLED)
            .order_by("appointment_date", "start_time")
        )

    return render(
        request,
        "appointments/doctor_appointments.html",
        {"appointments": appointments, "scope": scope},
    )


@doctor_profile_required
def doctor_appointment_detail(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient"),
        pk=pk,
        doctor=request.doctor,
    )

    return render(
        request,
        "appointments/appointment_detail.html",
        {
            "appointment": appointment,
            "patient": appointment.patient,
            "patient_profile": getattr(
                appointment.patient, "patient_profile", None
            ),
            "can_close": (
                appointment.status == Appointment.Status.CONFIRMED
                and has_started(appointment)
            ),
        },
    )


@require_POST
@doctor_profile_required
def update_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.doctor)
    new_status = request.POST.get("status")
    allowed = (Appointment.Status.COMPLETED, Appointment.Status.NO_SHOW)

    if new_status not in allowed:
        messages.error(request, "وضعیت انتخاب‌شده نامعتبر است.")
    elif appointment.status != Appointment.Status.CONFIRMED:
        messages.error(request, "وضعیت این نوبت قابل تغییر نیست.")
    elif not has_started(appointment):
        messages.error(request, "زمان این نوبت هنوز نرسیده است.")
    else:
        appointment.status = new_status
        appointment.save()
        messages.success(request, "وضعیت نوبت به‌روزرسانی شد.")

    return redirect("appointments:doctor_detail", pk=appointment.pk)