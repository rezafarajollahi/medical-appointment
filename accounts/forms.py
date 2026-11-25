import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import PatientProfile, User


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class TimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%H:%M")
        super().__init__(**kwargs)


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "national_id",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if phone and not re.fullmatch(r"09[0-9]{9}", phone):
            raise forms.ValidationError(
                "شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود."
            )
        return phone

    def clean_national_id(self):
        national_id = self.cleaned_data.get("national_id")
        if national_id and not re.fullmatch(r"[0-9]{10}", national_id):
            raise forms.ValidationError("کد ملی باید ۱۰ رقم باشد.")
        return national_id


class PatientProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = (
            "date_of_birth",
            "gender",
            "address",
            "medical_notes",
            "emergency_phone",
        )
        widgets = {
            "date_of_birth": DateInput(),
            "address": forms.Textarea(attrs={"rows": 2}),
            "medical_notes": forms.Textarea(attrs={"rows": 3}),
        }