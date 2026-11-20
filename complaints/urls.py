# complaints/urls.py
from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('submit/', views.create_complaint_view, name='submit'),
    path('<int:complaint_id>/', views.complaint_detail_view, name='detail'),
    path('<int:complaint_id>/edit/', views.edit_complaint_view, name='edit'),
    path('<int:complaint_id>/cancel/', views.cancel_complaint_view, name='cancel'),
    path('<int:complaint_id>/upload-evidence/', views.upload_evidence_view, name='upload_evidence'),
    path('evidence/<int:evidence_id>/download/', views.secure_evidence_download, name='download_evidence'),
    path('<int:complaint_id>/download-pdf/', views.download_complaint_pdf, name='download_pdf'),
    # Phase 05 Actions
    path('<int:complaint_id>/assign/', views.assign_investigator_action, name='assign'),
    path('<int:complaint_id>/update-status/', views.update_status_action, name='update_status'),
    path('<int:complaint_id>/add-note/', views.add_note_action, name='add_note'),
]