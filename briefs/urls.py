from django.urls import path

from . import views

app_name = "briefs"

urlpatterns = [
    path("", views.index, name="index"),
    path("healthz", views.healthz, name="healthz"),
    path("favicon.ico", views.favicon, name="favicon"),
    path("api/briefs/", views.generate_brief, name="generate"),
    path("api/events/", views.log_event, name="events"),
]
