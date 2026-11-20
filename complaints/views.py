# complaints/views.py

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.http import require_POST
from django.http import FileResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse

from .models import Complaint, Evidence
from .forms import ComplaintForm, EvidenceForm, AssignInvestigatorForm, StatusUpdateForm, NoteForm
from . import services

User = get_user_model()

@login_required
def create_complaint_view(request):
    if request.user.role != 'COMPLAINANT':
        raise PermissionDenied("Only complainants can submit new complaints.")

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            try:
                # 1. Create the Complaint via Service
                complaint = services.create_complaint(
                    actor=request.user,
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    category=form.cleaned_data['category']
                )
                
                # 2. Handle Evidence Upload if file exists
                uploaded_file = request.FILES.get('evidence')
                if uploaded_file:
                    evidence_form = EvidenceForm(request.POST, request.FILES)
                    if evidence_form.is_valid():
                        evidence = evidence_form.save(commit=False)
                        evidence.complaint = complaint
                        evidence.uploaded_by = request.user
                        evidence.save()
                        # Log the upload
                        services._create_activity_log(
                            complaint=complaint,
                            actor=request.user,
                            action_type='NOTE',
                            note=f"Uploaded initial evidence: {uploaded_file.name}",
                            is_internal=False
                        )
                    else:
                        # If file is invalid, show error but keep the complaint
                        messages.warning(request, f"Complaint created, but evidence failed: {evidence_form.errors.as_text()}")

                messages.success(request, f"Complaint submitted successfully! Tracking ID: {complaint.tracking_id}")
                return redirect('dashboard:complainant')
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "An unexpected error occurred. Please try again.")
    else:
        form = ComplaintForm()

    return render(request, 'complaints/submit_complaint.html', {'form': form})


@login_required
def complaint_detail_view(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user.role == 'COMPLAINANT' and complaint.complainant != request.user:
        raise PermissionDenied("Access denied.")
    elif request.user.role == 'INVESTIGATOR' and complaint.assigned_investigator != request.user:
        raise PermissionDenied("Access denied.")

    logs = complaint.activity_logs.all().order_by('-created_at')
    if request.user.role == 'COMPLAINANT':
        logs = logs.filter(is_internal=False)

    allowed_status_choices = []
    form_investigators = []
    
    if request.user.role in ['ADMIN', 'INVESTIGATOR']:
        raw_choices = complaint.ALLOWED_TRANSITIONS.get(complaint.status, [])
        if request.user.role == 'INVESTIGATOR':
            inv_allowed = ['INVESTIGATING', 'ON_HOLD', 'RESOLVED']
            raw_choices = [s for s in raw_choices if s.value in inv_allowed]
        allowed_status_choices = [(s.value, s.label) for s in raw_choices]

    if request.user.role == 'ADMIN':
        form_investigators = User.objects.filter(role='INVESTIGATOR', is_active=True)

    context = {
        'complaint': complaint,
        'logs': logs,
        'allowed_status_choices': allowed_status_choices,
        'form_investigators': form_investigators,
    }
    return render(request, 'complaints/complaint_detail.html', context)


@login_required
def edit_complaint_view(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user != complaint.complainant or complaint.status not in ['SUBMITTED', 'UNDER_REVIEW']:
        raise PermissionDenied("You cannot edit this complaint.")

    if request.method == 'POST':
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            try:
                services.update_complaint(
                    complaint_id=complaint.id,
                    actor=request.user,
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    category=form.cleaned_data['category']
                )
                messages.success(request, "Complaint updated successfully!")
                return redirect('complaints:detail', complaint_id=complaint.id)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = ComplaintForm(instance=complaint)

    return render(request, 'complaints/edit_complaint.html', {'form': form, 'complaint': complaint})


@login_required
@require_POST
def cancel_complaint_view(request, complaint_id):
    try:
        services.cancel_complaint(complaint_id=complaint_id, actor=request.user)
        messages.success(request, "Complaint cancelled and archived successfully.")
    except (PermissionDenied, ValidationError) as e:
        messages.error(request, str(e))
    return redirect('dashboard:complainant')


@login_required
def upload_evidence_view(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user.role == 'COMPLAINANT' and complaint.complainant != request.user:
        raise PermissionDenied("Access denied.")
    elif request.user.role == 'INVESTIGATOR' and complaint.assigned_investigator != request.user:
        raise PermissionDenied("Access denied.")

    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.complaint = complaint
            evidence.uploaded_by = request.user
            evidence.save()
            
            services._create_activity_log(
                complaint=complaint,
                actor=request.user,
                action_type='NOTE',
                note=f"Uploaded new evidence: {os.path.basename(evidence.file.name)}",
                is_internal=False
            )
            messages.success(request, "Evidence uploaded successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    
    return redirect('complaints:detail', complaint_id=complaint.id)


@login_required
def secure_evidence_download(request, evidence_id):
    evidence = get_object_or_404(Evidence, id=evidence_id)
    complaint = evidence.complaint

    is_authorized = False
    if request.user.role == 'ADMIN':
        is_authorized = True
    elif request.user.role == 'COMPLAINANT' and complaint.complainant == request.user:
        is_authorized = True
    elif request.user.role == 'INVESTIGATOR' and complaint.assigned_investigator == request.user:
        is_authorized = True

    if not is_authorized:
        raise PermissionDenied("You do not have permission to access this file.")

    file_path = evidence.file.path
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    else:
        raise FileNotFoundError("File not found on server.")


@login_required
@require_POST
def assign_investigator_action(request, complaint_id):
    if request.user.role != 'ADMIN':
        raise PermissionDenied("Only admins can assign investigators.")
        
    form = AssignInvestigatorForm(request.POST)
    if form.is_valid():
        try:
            services.assign_investigator(
                complaint_id=complaint_id,
                investigator=form.cleaned_data['investigator'],
                actor=request.user
            )
            messages.success(request, "Investigator assigned successfully.")
        except (ValidationError, PermissionDenied) as e:
            messages.error(request, str(e))
    else:
        messages.error(request, "Invalid investigator selection.")
    return redirect('complaints:detail', complaint_id=complaint_id)


@login_required
@require_POST
def update_status_action(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    allowed_transitions = complaint.ALLOWED_TRANSITIONS.get(complaint.status, [])
    if request.user.role == 'INVESTIGATOR':
        inv_allowed = ['INVESTIGATING', 'ON_HOLD', 'RESOLVED']
        allowed_transitions = [s for s in allowed_transitions if s.value in inv_allowed]
        
    choices = [(s.value, s.label) for s in allowed_transitions]
    
    if not choices:
        messages.error(request, "No further status transitions are allowed for your role.")
        return redirect('complaints:detail', complaint_id=complaint_id)

    form = StatusUpdateForm(request.POST, allowed_choices=choices)
    if form.is_valid():
        try:
            services.transition_complaint_status(
                complaint_id=complaint_id,
                new_status=form.cleaned_data['new_status'],
                actor=request.user,
                note=form.cleaned_data['note'],
                is_internal=False
            )
            messages.success(request, f"Status updated to {form.cleaned_data['new_status']}.")
        except (ValidationError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect('complaints:detail', complaint_id=complaint_id)


@login_required
@require_POST
def add_note_action(request, complaint_id):
    form = NoteForm(request.POST)
    if form.is_valid():
        try:
            services.add_internal_note(
                complaint_id=complaint_id,
                actor=request.user,
                note=form.cleaned_data['note']
            )
            messages.success(request, "Note added successfully.")
        except (ValidationError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect('complaints:detail', complaint_id=complaint_id)





# ... (keep your existing views) ...

@login_required
def download_complaint_pdf(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Security Check (Only complainant, assigned investigator, or admin can download)
    is_authorized = False
    if request.user.role == 'ADMIN':
        is_authorized = True
    elif request.user.role == 'COMPLAINANT' and complaint.complainant == request.user:
        is_authorized = True
    elif request.user.role == 'INVESTIGATOR' and complaint.assigned_investigator == request.user:
        is_authorized = True

    if not is_authorized:
        raise PermissionDenied("You do not have permission to download this report.")

    # Fetch Activity Logs (Hide internal notes if user is complainant)
    logs = complaint.activity_logs.all().order_by('created_at')
    if request.user.role == 'COMPLAINANT':
        logs = logs.filter(is_internal=False)

    # Render the HTML template
    html_string = render_to_string('complaints/pdf_report.html', {
        'complaint': complaint,
        'logs': logs,
        'user': request.user
    })

    # Generate PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Create HTTP Response with PDF headers
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Proofly_Report_{complaint.tracking_id}.pdf"'
    
    return response