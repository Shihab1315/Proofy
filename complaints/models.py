# complaints/models.py

import secrets
import os
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class ActiveComplaintManager(models.Manager):
    """
    Custom manager that returns only non-archived complaints.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class Complaint(models.Model):
    class CategoryChoices(models.TextChoices):
        THEFT = "THEFT", "Theft/Robbery"
        FRAUD = "FRAUD", "Financial Fraud/Scam"
        CYBERCRIME = "CYBERCRIME", "Cybercrime"
        HARASSMENT = "HARASSMENT", "Harassment"
        CORRUPTION = "CORRUPTION", "Corruption"
        OTHER = "OTHER", "Other"

    class StatusChoices(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        ASSIGNED = "ASSIGNED", "Assigned"
        INVESTIGATING = "INVESTIGATING", "Investigating"
        ON_HOLD = "ON_HOLD", "On Hold"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REJECTED = "REJECTED", "Rejected"

    class PriorityChoices(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    ALLOWED_TRANSITIONS = {
        StatusChoices.SUBMITTED: [StatusChoices.UNDER_REVIEW, StatusChoices.REJECTED],
        StatusChoices.UNDER_REVIEW: [StatusChoices.ASSIGNED, StatusChoices.REJECTED],
        StatusChoices.ASSIGNED: [StatusChoices.INVESTIGATING],
        StatusChoices.INVESTIGATING: [StatusChoices.ON_HOLD, StatusChoices.RESOLVED],
        StatusChoices.ON_HOLD: [StatusChoices.INVESTIGATING],
        StatusChoices.RESOLVED: [StatusChoices.CLOSED],
        StatusChoices.CLOSED: [],
        StatusChoices.REJECTED: [],
    }

    tracking_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.SUBMITTED)
    priority = models.CharField(max_length=10, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)
    
    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='filed_complaints')
    assigned_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_complaints', limit_choices_to={'role': 'INVESTIGATOR'}
    )
    
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active_objects = ActiveComplaintManager()

    def clean(self):
        super().clean()
        if self.assigned_investigator and self.assigned_investigator.role != 'INVESTIGATOR':
            raise ValidationError({'assigned_investigator': 'The assigned user must have the INVESTIGATOR role.'})

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = f"PRF-{secrets.token_hex(6).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_id} - {self.title}"


class ActivityLog(models.Model):
    class ActionTypeChoices(models.TextChoices):
        # Complaint Actions
        CREATION = "CREATION", "Complaint Created"
        STATUS_CHANGE = "STATUS_CHANGE", "Status Changed"
        ASSIGNMENT = "ASSIGNMENT", "Investigator Assigned"
        NOTE = "NOTE", "Note Added"
        ARCHIVED = "ARCHIVED", "Complaint Archived"
        UPDATE = "UPDATE", "Complaint Updated" 
        
        # System-Level Investigator Actions (Phase 05 Addition)
        INVESTIGATOR_CREATED = "INVESTIGATOR_CREATED", "Investigator Created"
        INVESTIGATOR_UPDATED = "INVESTIGATOR_UPDATED", "Investigator Updated"
        INVESTIGATOR_ACTIVATED = "INVESTIGATOR_ACTIVATED", "Investigator Activated"
        INVESTIGATOR_DEACTIVATED = "INVESTIGATOR_DEACTIVATED", "Investigator Deactivated"

    # Changed to null=True to support system events
    complaint = models.ForeignKey(
        Complaint, on_delete=models.PROTECT, null=True, blank=True, related_name='activity_logs'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_actions'
    )
    
    actor_username = models.CharField(max_length=150)
    actor_display_name = models.CharField(max_length=255, blank=True)
    
    action_type = models.CharField(max_length=30, choices=ActionTypeChoices.choices) # Increased max_length
    
    previous_status = models.CharField(max_length=20, choices=Complaint.StatusChoices.choices, blank=True, null=True)
    new_status = models.CharField(max_length=20, choices=Complaint.StatusChoices.choices, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Activity logs cannot be modified once created.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Activity logs cannot be deleted.")

    def __str__(self):
        target = self.complaint.tracking_id if self.complaint else "System Event"
        return f"Log for {target} by {self.actor_username} at {self.created_at}"
    
    
def evidence_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('evidence', str(instance.complaint.id), new_filename)


class Evidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='evidences')
    file = models.FileField(upload_to=evidence_upload_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_evidence')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Evidence for {self.complaint.tracking_id} - {os.path.basename(self.file.name)}"