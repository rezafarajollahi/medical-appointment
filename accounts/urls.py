from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="form_page.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
            extra_context={"title": "ورود به سامانه", "submit_label": "ورود"},
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/patient/", views.signup_patient, name="signup_patient"),
    path("signup/doctor/", views.signup_doctor, name="signup_doctor"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.patient_profile_edit, name="patient_profile"),
]