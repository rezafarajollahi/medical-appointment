from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin, DateInput, TimeInput

from .models import DoctorAvailability, DoctorProfile, DoctorTimeOff, Specialty


class DoctorSearchForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        label="نام پزشک",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "نام پزشک"}),
    )
    specialty = forms.ModelChoiceField(
        label="تخصص",
        queryset=Specialty.objects.filter(is_active=True),
        required=False,
        empty_label="همه تخصص‌ها",
    )


class DoctorProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = (
            "specialty",
            "medical_code",
            "bio",
            "clinic_name",
            "clinic_address",
            "clinic_phone",
            "visit_fee",
            "visit_duration",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "clinic_address": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["specialty"].queryset = Specialty.objects.filter(is_active=True)


class DoctorAvailabilityForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ("weekday", "start_time", "end_time", "valid_from", "valid_to")
        widgets = {
            "start_time": TimeInput(),
            "end_time": TimeInput(),
            "valid_from": DateInput(),
            "valid_to": DateInput(),
        }


class DoctorTimeOffForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DoctorTimeOff
        fields = ("date", "start_time", "end_time", "reason")
        widgets = {
            "date": DateInput(),
            "start_time": TimeInput(),
            "end_time": TimeInput(),
        }

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.localdate():
            raise forms.ValidationError("تاریخ عدم حضور نمی‌تواند در گذشته باشد.")
        return date