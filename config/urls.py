from django.contrib import admin
from django.urls import include, path
from doctors import views as doctor_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", doctor_views.home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("doctors/", include("doctors.urls")),
    path("appointments/", include("appointments.urls")),
]
