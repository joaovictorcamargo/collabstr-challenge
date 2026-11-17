from django.urls import include, path

urlpatterns = [
    path("", include("briefs.urls")),
]
