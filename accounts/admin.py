from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PatientProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "اطلاعات تکمیلی",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "national_id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "اطلاعات تکمیلی",
            {
                "fields": (
                    "email",
                    "role",
                    "phone_number",
                    "national_id",
                )
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "national_id",
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date_of_birth",
        "gender",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__phone_number",
    )

#ss