# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'
admin_dashboard = getattr(views, 'admin_dashboard', views.dashboard_redirect)

urlpatterns = [
    path('', views.dashboard_redirect, name='home'),
    path('complainant/', views.complainant_dashboard, name='complainant'),
    path('investigator/', views.investigator_dashboard, name='investigator'),
    path('admin/', admin_dashboard, name='admin'),
]