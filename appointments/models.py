from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from doctors.models import DoctorProfile


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار تأیید"
        CONFIRMED = "confirmed", "تأیید شده"
        CANCELLED = "cancelled", "لغو شده"
        COMPLETED = "completed", "تکمیل شده"
        NO_SHOW = "no_show", "عدم مراجعه بیمار"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="بیمار",
        on_delete=models.CASCADE,
        related_name="patient_appointments",
    )

    doctor = models.ForeignKey(
        DoctorProfile,
        verbose_name="پزشک",
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    appointment_date = models.DateField(
        verbose_name="تاریخ نوبت",
    )

    start_time = models.TimeField(
        verbose_name="ساعت شروع",
    )

    end_time = models.TimeField(
        verbose_name="ساعت پایان",
    )

    status = models.CharField(
        verbose_name="وضعیت",
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    patient_description = models.TextField(
        verbose_name="توضیحات بیمار",
        blank=True,
        help_text="توضیحات مختصر درباره علت مراجعه",
    )

    cancellation_reason = models.TextField(
        verbose_name="دلیل لغو",
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        verbose_name="زمان لغو",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ثبت نوبت",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="آخرین ویرایش",
        auto_now=True,
    )

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        ordering = ["-appointment_date", "-start_time"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "doctor",
                    "appointment_date",
                    "start_time",
                ],
                name="unique_doctor_appointment_slot",
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "doctor",
                    "appointment_date",
                    "status",
                ],
                name="doctor_date_status_idx",
            ),
            models.Index(
                fields=[
                    "patient",
                    "appointment_date",
                ],
                name="patient_date_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.patient_id and self.patient.role != "patient":
            raise ValidationError(
                {
                    "patient": "فقط کاربری با نقش بیمار می‌تواند نوبت دریافت کند."
                }
            )

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    {
                        "end_time": "ساعت پایان باید بعد از ساعت شروع باشد."
                    }
                )

        if self.doctor_id:
            if not self.doctor.is_active:
                raise ValidationError(
                    {
                        "doctor": "این پزشک در حال حاضر فعال نیست."
                    }
                )

            if not self.doctor.is_verified:
                raise ValidationError(
                    {
                        "doctor": "این پزشک هنوز توسط مدیر سیستم تأیید نشده است."
                    }
                )

    def __str__(self):
        return (
            f"{self.patient} - {self.doctor} - "
            f"{self.appointment_date} {self.start_time}"
        )


class Review(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        verbose_name="نوبت",
        on_delete=models.CASCADE,
        related_name="review",
    )

    rating = models.PositiveSmallIntegerField(
        verbose_name="امتیاز",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    comment = models.TextField(
        verbose_name="نظر",
        blank=True,
    )

    is_visible = models.BooleanField(
        verbose_name="قابل نمایش",
        default=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ثبت",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="آخرین ویرایش",
        auto_now=True,
    )

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()

        if (
            self.appointment_id
            and self.appointment.status != Appointment.Status.COMPLETED
        ):
            raise ValidationError(
                {
                    "appointment": (
                        "ثبت نظر فقط برای نوبت تکمیل‌شده امکان‌پذیر است."
                    )
                }
            )

    @property
    def doctor(self):
        return self.appointment.doctor

    @property
    def patient(self):
        return self.appointment.patient

    def __str__(self):
        return (
            f"امتیاز {self.rating} برای "
            f"{self.appointment.doctor}"
        )


class AppointmentNotification(models.Model):
    class NotificationType(models.TextChoices):
        CONFIRMATION = "confirmation", "تأیید نوبت"
        REMINDER = "reminder", "یادآوری نوبت"
        CANCELLATION = "cancellation", "لغو نوبت"

    class Channel(models.TextChoices):
        EMAIL = "email", "ایمیل"
        SMS = "sms", "پیامک"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار ارسال"
        SENT = "sent", "ارسال شده"
        FAILED = "failed", "ناموفق"

    appointment = models.ForeignKey(
        Appointment,
        verbose_name="نوبت",
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="دریافت‌کننده",
        on_delete=models.CASCADE,
        related_name="appointment_notifications",
    )

    notification_type = models.CharField(
        verbose_name="نوع پیام",
        max_length=20,
        choices=NotificationType.choices,
    )

    channel = models.CharField(
        verbose_name="روش ارسال",
        max_length=10,
        choices=Channel.choices,
        default=Channel.EMAIL,
    )

    status = models.CharField(
        verbose_name="وضعیت ارسال",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    error_message = models.TextField(
        verbose_name="متن خطا",
        blank=True,
    )

    scheduled_at = models.DateTimeField(
        verbose_name="زمان برنامه‌ریزی‌شده",
        null=True,
        blank=True,
    )

    sent_at = models.DateTimeField(
        verbose_name="زمان ارسال",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ایجاد",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "پیام نوبت"
        verbose_name_plural = "پیام‌های نوبت"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_notification_type_display()} - "
            f"{self.recipient}"
        )