from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import PatientProfile, User
from appointments.models import Appointment, Review
from appointments.services import (
    BookingError,
    book_appointment,
    cancel_appointment,
    get_free_slots,
    model_weekday,
)
from doctors.models import DoctorAvailability, DoctorProfile, Specialty

PASSWORD = "Test@12345"

SPECIALTIES = [
    ("قلب و عروق", "cardiology"),
    ("پوست و مو", "dermatology"),
    ("کودکان", "pediatrics"),
    ("ارتوپدی", "orthopedics"),
    ("چشم‌پزشکی", "ophthalmology"),
]

DOCTORS = [
    ("dr_ahmadi", "سارا", "احمدی", "cardiology", 400000, 30, True,
     [0, 2, 4], [(time(9, 0), time(12, 0))]),
    ("dr_karimi", "رضا", "کریمی", "dermatology", 350000, 20, True,
     [1, 3], [(time(16, 0), time(19, 0))]),
    ("dr_mousavi", "مریم", "موسوی", "pediatrics", 300000, 20, True,
     [0, 1, 2, 3, 4], [(time(8, 30), time(11, 30))]),
    ("dr_rahimi", "حسین", "رحیمی", "orthopedics", 450000, 30, False,
     [5], [(time(10, 0), time(13, 0))]),
]

PATIENTS = [
    ("patient1", "علی", "محمدی"),
    ("patient2", "زهرا", "حسینی"),
    ("patient3", "امیر", "نوری"),
]


class Command(BaseCommand):
    help = "ورود داده‌های تستی پروژه نوبت‌دهی"

    def _user(self, username, first_name, last_name, role, index):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{username}@example.com",
                "role": role,
                "phone_number": f"0912000{index:04d}",
                "national_id": f"{index:010d}",
            },
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        return user

    def _add_minutes(self, day, start, minutes):
        return (datetime.combine(day, start) + timedelta(minutes=minutes)).time()

    def _past_day(self, doctor):
        weekdays = set(doctor.availabilities.values_list("weekday", flat=True))
        day = timezone.localdate() - timedelta(days=1)
        for _ in range(7):
            if model_weekday(day) in weekdays:
                return day
            day -= timedelta(days=1)
        return None

    def _book_first_free(self, patient, doctor, description):
        already = Appointment.objects.filter(
            patient=patient,
            doctor=doctor,
            appointment_date__gte=timezone.localdate(),
        ).exists()
        if already:
            return None

        days = get_free_slots(doctor)
        if not days:
            return None

        try:
            return book_appointment(
                patient=patient,
                doctor=doctor,
                day=days[0]["date"],
                start_time=days[0]["slots"][0]["start"],
                description=description,
            )
        except BookingError as error:
            self.stdout.write(self.style.WARNING(str(error)))
            return None

    @transaction.atomic
    def handle(self, *args, **options):
        specialties = {}
        for name, slug in SPECIALTIES:
            specialties[slug], _ = Specialty.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )

        doctors = []
        for index, row in enumerate(DOCTORS, start=1):
            username, first, last, slug, fee, duration, verified, weekdays, hours = row
            user = self._user(username, first, last, User.Role.DOCTOR, index)

            doctor, _ = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "specialty": specialties[slug],
                    "medical_code": f"NP-{1000 + index}",
                    "bio": "پزشک نمونه برای داده تستی.",
                    "clinic_name": f"مطب دکتر {last}",
                    "clinic_address": "تهران، خیابان ولیعصر، ساختمان پزشکان",
                    "clinic_phone": "02188000000",
                    "visit_fee": fee,
                    "visit_duration": duration,
                    "is_verified": verified,
                },
            )

            for weekday in weekdays:
                for start, end in hours:
                    DoctorAvailability.objects.get_or_create(
                        doctor=doctor,
                        weekday=weekday,
                        start_time=start,
                        end_time=end,
                    )

            doctors.append(doctor)

        patients = []
        for index, (username, first, last) in enumerate(PATIENTS, start=11):
            user = self._user(username, first, last, User.Role.PATIENT, index)
            PatientProfile.objects.get_or_create(user=user)
            patients.append(user)

        patient1, patient2, patient3 = patients
        doctor1, doctor2 = doctors[0], doctors[1]

        past_day = self._past_day(doctor1)
        if past_day:
            availability = (
                doctor1.availabilities.filter(weekday=model_weekday(past_day))
                .order_by("start_time")
                .first()
            )
            start1 = availability.start_time
            start2 = self._add_minutes(past_day, start1, doctor1.visit_duration)
            start3 = self._add_minutes(past_day, start2, doctor1.visit_duration)

            completed, _ = Appointment.objects.get_or_create(
                doctor=doctor1,
                appointment_date=past_day,
                start_time=start1,
                defaults={
                    "patient": patient1,
                    "end_time": start2,
                    "status": Appointment.Status.COMPLETED,
                    "patient_description": "چکاپ دوره‌ای",
                },
            )
            Review.objects.get_or_create(
                appointment=completed,
                defaults={"rating": 5, "comment": "برخورد بسیار خوب و دقیق."},
            )

            Appointment.objects.get_or_create(
                doctor=doctor1,
                appointment_date=past_day,
                start_time=start2,
                defaults={
                    "patient": patient2,
                    "end_time": start3,
                    "status": Appointment.Status.CONFIRMED,
                    "patient_description": "تپش قلب",
                },
            )

        self._book_first_free(patient1, doctor1, "ادامه درمان")
        self._book_first_free(patient2, doctor2, "مشکل پوستی")

        to_cancel = self._book_first_free(patient3, doctor1, "معاینه")
        if to_cancel:
            cancel_appointment(to_cancel, "تغییر برنامه شخصی")

        self.stdout.write(self.style.SUCCESS("داده‌های تستی وارد شدند."))
        self.stdout.write(f"رمز همه کاربران تستی: {PASSWORD}")
        self.stdout.write("پزشکان: dr_ahmadi, dr_karimi, dr_mousavi, dr_rahimi (تأییدنشده)")
        self.stdout.write("بیماران: patient1, patient2, patient3")