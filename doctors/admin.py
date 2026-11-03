from django.contrib import admin

from .models import (
    DoctorAvailability,
    DoctorProfile,
    DoctorTimeOff,
    Specialty,
)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "specialty",
        "medical_code",
        "is_verified",
        "is_active",
    )

    list_filter = (
        "specialty",
        "is_verified",
        "is_active",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "medical_code",
        "clinic_name",
    )

    autocomplete_fields = (
        "user",
        "specialty",
    )


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "weekday",
        "start_time",
        "end_time",
        "is_active",
    )

    list_filter = (
        "weekday",
        "is_active",
    )

    autocomplete_fields = ("doctor",)


@admin.register(DoctorTimeOff)
class DoctorTimeOffAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "date",
        "start_time",
        "end_time",
    )

    list_filter = ("date",)
    autocomplete_fields = ("doctor",)
