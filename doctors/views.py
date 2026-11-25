from django.contrib import messages
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import doctor_profile_required, doctor_required
from appointments.models import Appointment, Review
from appointments.services import get_free_slots

from .forms import (
    DoctorAvailabilityForm,
    DoctorProfileForm,
    DoctorSearchForm,
    DoctorTimeOffForm,
)
from .models import DoctorAvailability, DoctorProfile, DoctorTimeOff, Specialty


def _public_doctors():
    return (
        DoctorProfile.objects.filter(
            is_active=True,
            is_verified=True,
            user__is_active=True,
        )
        .select_related("user", "specialty")
        .annotate(
            avg_rating=Avg(
                "appointments__review__rating",
                filter=Q(appointments__review__is_visible=True),
            )
        )
    )


def home(request):
    return render(
        request,
        "home.html",
        {
            "form": DoctorSearchForm(),
            "specialties": Specialty.objects.filter(is_active=True),
        },
    )


def doctor_list(request):
    form = DoctorSearchForm(request.GET or None)
    doctors = _public_doctors()

    if form.is_valid():
        for term in form.cleaned_data["q"].split():
            doctors = doctors.filter(
                Q(user__first_name__icontains=term)
                | Q(user__last_name__icontains=term)
            )

        specialty = form.cleaned_data["specialty"]
        if specialty:
            doctors = doctors.filter(specialty=specialty)

    return render(
        request,
        "doctors/doctor_list.html",
        {"form": form, "doctors": doctors},
    )


def doctor_detail(request, pk):
    doctor = get_object_or_404(_public_doctors(), pk=pk)
    reviews = Review.objects.filter(
        appointment__doctor=doctor,
        is_visible=True,
    ).select_related("appointment__patient")

    return render(
        request,
        "doctors/doctor_detail.html",
        {
            "doctor": doctor,
            "days": get_free_slots(doctor),
            "reviews": reviews,
        },
    )


@doctor_profile_required
def dashboard(request):
    doctor = request.doctor
    today = timezone.localdate()
    active = doctor.appointments.exclude(status=Appointment.Status.CANCELLED)

    return render(
        request,
        "doctors/dashboard.html",
        {
            "doctor": doctor,
            "today_appointments": active.filter(appointment_date=today)
            .select_related("patient")
            .order_by("start_time"),
            "upcoming_count": active.filter(
                appointment_date__gte=today,
                status=Appointment.Status.CONFIRMED,
            ).count(),
            "total_count": doctor.appointments.count(),
        },
    )


@doctor_required
def profile_edit(request):
    profile = getattr(request.user, "doctor_profile", None)
    if profile is None:
        profile = DoctorProfile(user=request.user)

    form = DoctorProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "مشخصات شما ذخیره شد.")
        return redirect("doctors:dashboard")

    return render(
        request,
        "form_page.html",
        {"form": form, "title": "مشخصات و تخصص پزشک", "submit_label": "ذخیره"},
    )


@doctor_profile_required
def schedule(request):
    doctor = request.doctor
    return render(
        request,
        "doctors/schedule.html",
        {
            "availabilities": doctor.availabilities.all(),
            "times_off": doctor.times_off.filter(date__gte=timezone.localdate()),
        },
    )


@doctor_profile_required
def availability_create(request):
    form = DoctorAvailabilityForm(
        request.POST or None,
        instance=DoctorAvailability(doctor=request.doctor),
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "برنامه حضور ثبت شد.")
        return redirect("doctors:schedule")

    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "افزودن روز و ساعت حضور",
            "description": "تاریخ‌های اعتبار اختیاری هستند.",
        },
    )


@require_POST
@doctor_profile_required
def availability_delete(request, pk):
    get_object_or_404(DoctorAvailability, pk=pk, doctor=request.doctor).delete()
    messages.success(request, "برنامه حضور حذف شد.")
    return redirect("doctors:schedule")


@doctor_profile_required
def timeoff_create(request):
    form = DoctorTimeOffForm(
        request.POST or None,
        instance=DoctorTimeOff(doctor=request.doctor),
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "زمان عدم حضور ثبت شد.")
        return redirect("doctors:schedule")

    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "ثبت زمان عدم حضور",
            "description": "اگر ساعت‌ها را خالی بگذارید، کل روز تعطیل می‌شود.",
        },
    )


@require_POST
@doctor_profile_required
def timeoff_delete(request, pk):
    get_object_or_404(DoctorTimeOff, pk=pk, doctor=request.doctor).delete()
    messages.success(request, "زمان عدم حضور حذف شد.")
    return redirect("doctors:schedule")