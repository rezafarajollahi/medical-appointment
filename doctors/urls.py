from django.urls import path

from . import views

app_name = "doctors"

urlpatterns = [
    path("", views.doctor_list, name="list"),
    path("<int:pk>/", views.doctor_detail, name="detail"),
    path("panel/", views.dashboard, name="dashboard"),
    path("panel/profile/", views.profile_edit, name="profile_edit"),
    path("panel/schedule/", views.schedule, name="schedule"),
    path("panel/schedule/add/", views.availability_create, name="availability_create"),
    path(
        "panel/schedule/<int:pk>/delete/",
        views.availability_delete,
        name="availability_delete",
    ),
    path("panel/time-off/add/", views.timeoff_create, name="timeoff_create"),
    path(
        "panel/time-off/<int:pk>/delete/",
        views.timeoff_delete,
        name="timeoff_delete",
    ),
]