# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
     path('force-password-change/', views.force_password_change_view, name='force_password_change'),
    # Investigator Management URLs (Phase 05)
    path('investigators/', views.investigator_list_view, name='investigator_list'),
    path('investigators/create/', views.investigator_create_view, name='investigator_create'),
    path('investigators/<int:user_id>/', views.investigator_detail_view, name='investigator_detail'),
    path('investigators/<int:user_id>/edit/', views.investigator_edit_view, name='investigator_edit'),
    path('investigators/<int:user_id>/toggle-status/', views.investigator_toggle_status_view, name='investigator_toggle_status'),
]