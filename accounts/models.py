from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "patient", "بیمار"
        DOCTOR = "doctor", "پزشک"

    email = models.EmailField(
        verbose_name="ایمیل",
        unique=True,
    )

    phone_number = models.CharField(
        verbose_name="شماره تلفن",
        max_length=11,
        unique=True,
        null=True,
        blank=True,
    )

    national_id = models.CharField(
        verbose_name="کد ملی",
        max_length=10,
        unique=True,
        null=True,
        blank=True,
    )

    role = models.CharField(
        verbose_name="نقش",
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ایجاد حساب",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="آخرین ویرایش",
        auto_now=True,
    )

    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        full_name = self.get_full_name()

        if full_name:
            return full_name

        return self.username


class PatientProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "مرد"
        FEMALE = "female", "زن"
        OTHER = "other", "سایر"

    user = models.OneToOneField(
        User,
        verbose_name="کاربر",
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )

    date_of_birth = models.DateField(
        verbose_name="تاریخ تولد",
        null=True,
        blank=True,
    )

    gender = models.CharField(
        verbose_name="جنسیت",
        max_length=10,
        choices=Gender.choices,
        blank=True,
    )

    address = models.TextField(
        verbose_name="آدرس",
        blank=True,
    )

    medical_notes = models.TextField(
        verbose_name="توضیحات پزشکی",
        blank=True,
        help_text="مانند حساسیت دارویی یا بیماری زمینه‌ای",
    )

    emergency_phone = models.CharField(
        verbose_name="شماره تماس اضطراری",
        max_length=15,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ایجاد",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="آخرین ویرایش",
        auto_now=True,
    )

    class Meta:
        verbose_name = "پروفایل بیمار"
        verbose_name_plural = "پروفایل‌های بیماران"

    def __str__(self):
        return f"پروفایل بیمار: {self.user}"
