from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, "شما به این بخش دسترسی ندارید.")
                return redirect("home")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


patient_required = role_required("patient")
doctor_required = role_required("doctor")


def doctor_profile_required(view_func):
    @wraps(view_func)
    @doctor_required
    def wrapper(request, *args, **kwargs):
        doctor = getattr(request.user, "doctor_profile", None)
        if doctor is None:
            messages.warning(request, "ابتدا پروفایل پزشکی خود را تکمیل کنید.")
            return redirect("doctors:profile_edit")
        request.doctor = doctor
        return view_func(request, *args, **kwargs)

    return wrapper