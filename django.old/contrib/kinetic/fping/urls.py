from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name='home'),
    path("down", views.report_down),
    path("loss", views.report_loss),
    path("agent/", views.fping_collector),
    path("agent/<str:agent_id>", views.fping_agent),
    path("<str:agent_id>", views.report_agent),
    path("<str:agent_id>/<str:address_id>", views.graph_host),
]