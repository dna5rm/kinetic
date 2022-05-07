from django.urls import path
from . import views

urlpatterns = [
    path('', views.main),
    path("report/", views.report, name="report"),
]