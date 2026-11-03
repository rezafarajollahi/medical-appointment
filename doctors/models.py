from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Specialty(models.Model):
    name = models.CharField(
        verbose_name="نام تخصص",
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        verbose_name="نام انگلیسی در آدرس",
        max_length=120,
        unique=True,
    )

    description = models.TextField(
        verbose_name="توضیحات",
        blank=True,
    )

    is_active = models.BooleanField(
        verbose_name="فعال است",
        default=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ایجاد",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="کاربر",
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )

    specialty = models.ForeignKey(
        Specialty,
        verbose_name="تخصص",
        on_delete=models.PROTECT,
        related_name="doctors",
    )

    medical_code = models.CharField(
        verbose_name="شماره نظام پزشکی",
        max_length=30,
        unique=True,
    )

    bio = models.TextField(
        verbose_name="درباره پزشک",
        blank=True,
    )

    clinic_name = models.CharField(
        verbose_name="نام مطب یا مرکز درمانی",
        max_length=150,
        blank=True,
    )

    clinic_address = models.TextField(
        verbose_name="آدرس مطب",
    )

    clinic_phone = models.CharField(
        verbose_name="تلفن مطب",
        max_length=15,
        blank=True,
    )

    latitude = models.DecimalField(
        verbose_name="عرض جغرافیایی",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        verbose_name="طول جغرافیایی",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    visit_fee = models.DecimalField(
        verbose_name="هزینه ویزیت",
        max_digits=10,
        decimal_places=0,
        default=0,
    )

    visit_duration = models.PositiveSmallIntegerField(
        verbose_name="مدت هر ویزیت به دقیقه",
        default=20,
    )

    is_verified = models.BooleanField(
        verbose_name="تأیید شده",
        default=False,
    )

    is_active = models.BooleanField(
        verbose_name="فعال",
        default=True,
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
        verbose_name = "پروفایل پزشک"
        verbose_name_plural = "پروفایل‌های پزشکان"
        ordering = ["user__last_name", "user__first_name"]

    def clean(self):
        super().clean()

        if self.user_id and self.user.role != "doctor":
            raise ValidationError(
                {
                    "user": "فقط کاربری با نقش پزشک می‌تواند پروفایل پزشک داشته باشد."
                }
            )

        if self.visit_duration <= 0:
            raise ValidationError(
                {
                    "visit_duration": "مدت ویزیت باید بیشتر از صفر باشد."
                }
            )

    def __str__(self):
        return f"دکتر {self.user.get_full_name() or self.user.username}"


class DoctorAvailability(models.Model):
    class Weekday(models.IntegerChoices):
        SATURDAY = 0, "شنبه"
        SUNDAY = 1, "یکشنبه"
        MONDAY = 2, "دوشنبه"
        TUESDAY = 3, "سه‌شنبه"
        WEDNESDAY = 4, "چهارشنبه"
        THURSDAY = 5, "پنج‌شنبه"
        FRIDAY = 6, "جمعه"

    doctor = models.ForeignKey(
        DoctorProfile,
        verbose_name="پزشک",
        on_delete=models.CASCADE,
        related_name="availabilities",
    )

    weekday = models.PositiveSmallIntegerField(
        verbose_name="روز هفته",
        choices=Weekday.choices,
    )

    start_time = models.TimeField(
        verbose_name="ساعت شروع",
    )

    end_time = models.TimeField(
        verbose_name="ساعت پایان",
    )

    valid_from = models.DateField(
        verbose_name="معتبر از تاریخ",
        null=True,
        blank=True,
    )

    valid_to = models.DateField(
        verbose_name="معتبر تا تاریخ",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        verbose_name="فعال",
        default=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ایجاد",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "برنامه حضور پزشک"
        verbose_name_plural = "برنامه‌های حضور پزشکان"
        ordering = ["doctor", "weekday", "start_time"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "doctor",
                    "weekday",
                    "start_time",
                    "end_time",
                ],
                name="unique_doctor_weekday_time_range",
            )
        ]

    def clean(self):
        super().clean()

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    {
                        "end_time": "ساعت پایان باید بعد از ساعت شروع باشد."
                    }
                )

        if self.valid_from and self.valid_to:
            if self.valid_to < self.valid_from:
                raise ValidationError(
                    {
                        "valid_to": "تاریخ پایان اعتبار نمی‌تواند قبل از تاریخ شروع باشد."
                    }
                )

        if (
            self.doctor_id
            and self.weekday is not None
            and self.start_time
            and self.end_time
        ):
            overlapping = DoctorAvailability.objects.filter(
                doctor=self.doctor,
                weekday=self.weekday,
                is_active=True,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )

            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    "این بازه زمانی با یکی از برنامه‌های قبلی پزشک تداخل دارد."
                )

    def __str__(self):
        return (
            f"{self.doctor} - {self.get_weekday_display()} "
            f"از {self.start_time} تا {self.end_time}"
        )


class DoctorTimeOff(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile,
        verbose_name="پزشک",
        on_delete=models.CASCADE,
        related_name="times_off",
    )

    date = models.DateField(
        verbose_name="تاریخ عدم حضور",
    )

    start_time = models.TimeField(
        verbose_name="ساعت شروع",
        null=True,
        blank=True,
        help_text="در صورت خالی بودن، کل روز تعطیل در نظر گرفته می‌شود.",
    )

    end_time = models.TimeField(
        verbose_name="ساعت پایان",
        null=True,
        blank=True,
    )

    reason = models.CharField(
        verbose_name="دلیل",
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="زمان ایجاد",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "عدم حضور پزشک"
        verbose_name_plural = "زمان‌های عدم حضور پزشکان"
        ordering = ["date", "start_time"]

    def clean(self):
        super().clean()

        if bool(self.start_time) != bool(self.end_time):
            raise ValidationError(
                "ساعت شروع و پایان باید هر دو وارد شوند یا هر دو خالی باشند."
            )

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    {
                        "end_time": "ساعت پایان باید بعد از ساعت شروع باشد."
                    }
                )

    def __str__(self):
        if self.start_time and self.end_time:
            return (
                f"{self.doctor} - {self.date} "
                f"از {self.start_time} تا {self.end_time}"
            )

        return f"{self.doctor} - تعطیلی کامل در {self.date}"
