from django.contrib import admin

from .models import (
    Appointment,
    AppointmentNotification,
    Review,
)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "appointment_date",
        "start_time",
        "status",
    )

    list_filter = (
        "status",
        "appointment_date",
        "doctor__specialty",
    )

    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "patient__phone_number",
        "doctor__user__first_name",
        "doctor__user__last_name",
    )

    autocomplete_fields = (
        "patient",
        "doctor",
    )

    date_hierarchy = "appointment_date"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "rating",
        "is_visible",
        "created_at",
    )

    list_filter = (
        "rating",
        "is_visible",
    )

    autocomplete_fields = ("appointment",)


@admin.register(AppointmentNotification)
class AppointmentNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "recipient",
        "notification_type",
        "channel",
        "status",
        "scheduled_at",
        "sent_at",
    )

    list_filter = (
        "notification_type",
        "channel",
        "status",
    )

    autocomplete_fields = (
        "appointment",
        "recipient",
    )
