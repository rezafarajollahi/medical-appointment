from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path(
        "book/<int:doctor_id>/<str:date_str>/<str:time_str>/",
        views.book,
        name="book",
    ),
    path("mine/", views.my_appointments, name="my_appointments"),
    path("<int:pk>/cancel/", views.cancel, name="cancel"),
    path("<int:pk>/review/", views.review_create, name="review"),
    path("doctor/", views.doctor_appointments, name="doctor_list"),
    path("doctor/<int:pk>/", views.doctor_appointment_detail, name="doctor_detail"),
    path("doctor/<int:pk>/status/", views.update_status, name="update_status"),
]