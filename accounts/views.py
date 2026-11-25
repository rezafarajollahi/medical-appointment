from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import patient_required
from .forms import PatientProfileForm, SignUpForm
from .models import PatientProfile, User


def _signup(request, role, title):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.role = role
        user.save()
        login(request, user)

        if role == User.Role.PATIENT:
            PatientProfile.objects.create(user=user)
            messages.success(request, "ثبت‌نام با موفقیت انجام شد.")
            return redirect("doctors:list")

        messages.success(
            request,
            "ثبت‌نام انجام شد. لطفاً مشخصات و تخصص خود را تکمیل کنید.",
        )
        return redirect("doctors:profile_edit")

    return render(
        request,
        "form_page.html",
        {"form": form, "title": title, "submit_label": "ثبت‌نام"},
    )


def signup_patient(request):
    return _signup(request, User.Role.PATIENT, "ثبت‌نام بیمار")


def signup_doctor(request):
    return _signup(request, User.Role.DOCTOR, "ثبت‌نام پزشک")


@login_required
def dashboard(request):
    if request.user.role == User.Role.DOCTOR:
        return redirect("doctors:dashboard")
    return redirect("appointments:my_appointments")


@patient_required
def patient_profile_edit(request):
    profile, _ = PatientProfile.objects.get_or_create(user=request.user)
    form = PatientProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "اطلاعات شما ذخیره شد.")
        return redirect("appointments:my_appointments")

    return render(
        request,
        "form_page.html",
        {"form": form, "title": "اطلاعات تکمیلی بیمار", "submit_label": "ذخیره"},
    )