from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Review


class BookingForm(BootstrapFormMixin, forms.Form):
    patient_description = forms.CharField(
        label="علت مراجعه (اختیاری)",
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class CancelForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(
        label="دلیل لغو",
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ReviewForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(
                choices=[
                    (5, "۵ - عالی"),
                    (4, "۴ - خوب"),
                    (3, "۳ - متوسط"),
                    (2, "۲ - ضعیف"),
                    (1, "۱ - خیلی ضعیف"),
                ]
            ),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }