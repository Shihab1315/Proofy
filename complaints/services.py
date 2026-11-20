# complaints/services.py

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Complaint, ActivityLog

# -------------------------------------------------------------------------
# IMPORTANT NOTE ON DATABASE LOCKING (SQLite vs PostgreSQL):
# The `select_for_update()` method is used below to prevent race conditions 
# (e.g., two Admins changing the status at the exact same time).
# 
# SQLite does NOT support row-level locking. It will either lock the entire 
# database or ignore the command. This code is designed to be fully 
# compatible with PostgreSQL, where row-level locking works flawlessly.
# -------------------------------------------------------------------------

def _create_activity_log(complaint, actor, action_type, previous_status=None, new_status=None, note=None, is_internal=False):
    """
    Internal helper to safely create an ActivityLog with user snapshots.
    """
    ActivityLog.objects.create(
        complaint=complaint,
        actor=actor,
        actor_username=actor.username,
        actor_display_name=actor.get_full_name() or actor.username,
        action_type=action_type,
        previous_status=previous_status,
        new_status=new_status,
        note=note,
        is_internal=is_internal
    )


@transaction.atomic
def create_complaint(actor, title, description, category):
    """
    Creates a new complaint. 
    Enforces that the creator is a COMPLAINANT.
    """
    if actor.role != 'COMPLAINANT':
        raise PermissionDenied("Only complainants can file new complaints.")

    complaint = Complaint.objects.create(
        complainant=actor,
        title=title,
        description=description,
        category=category,
        status=Complaint.StatusChoices.SUBMITTED
    )
    
    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.CREATION,
        new_status=Complaint.StatusChoices.SUBMITTED,
        note="Complaint filed successfully."
    )
    
    return complaint


@transaction.atomic
def transition_complaint_status(complaint_id, new_status, actor, note=None, is_internal=False):
    """
    Safely transitions a complaint's status, enforcing role permissions 
    and the allowed transition map.
    """
    # Lock the row to prevent simultaneous status updates
    complaint = get_object_or_404(Complaint.objects.select_for_update(), id=complaint_id)
    previous_status = complaint.status

    if previous_status == new_status:
        raise ValidationError(f"Complaint is already in {new_status} status.")

    # 1. Check Transition Map
    allowed_next_statuses = Complaint.ALLOWED_TRANSITIONS.get(previous_status, [])
    if new_status not in allowed_next_statuses:
        raise ValidationError(f"Invalid status transition from {previous_status} to {new_status}.")

    # 2. Check Role Permissions
    if actor.role == 'ADMIN':
        pass # Admins can perform any valid transition
    elif actor.role == 'INVESTIGATOR':
        if complaint.assigned_investigator != actor:
            raise PermissionDenied("You can only update cases assigned to you.")
        
        # Investigators have restricted transitions
        investigator_allowed = [
            Complaint.StatusChoices.INVESTIGATING, 
            Complaint.StatusChoices.ON_HOLD, 
            Complaint.StatusChoices.RESOLVED
        ]
        if new_status not in investigator_allowed:
            raise PermissionDenied("Investigators are not authorized to make this status change.")
    else:
        raise PermissionDenied("Complainants cannot change complaint statuses.")

    # 3. Apply Change
    complaint.status = new_status
    complaint.save()

    # 4. Log Action
    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.STATUS_CHANGE,
        previous_status=previous_status,
        new_status=new_status,
        note=note,
        is_internal=is_internal
    )
    
    return complaint


@transaction.atomic
def assign_investigator(complaint_id, investigator, actor):
    """
    Assigns an investigator to a complaint. Admin only.
    """
    if actor.role != 'ADMIN':
        raise PermissionDenied("Only administrators can assign investigators.")
    
    if investigator.role != 'INVESTIGATOR':
        raise ValidationError("The assigned user must have the INVESTIGATOR role.")

    complaint = get_object_or_404(Complaint.objects.select_for_update(), id=complaint_id)
    complaint.assigned_investigator = investigator
    
    # Auto-transition status to ASSIGNED if it was UNDER_REVIEW
    previous_status = complaint.status
    if previous_status == Complaint.StatusChoices.UNDER_REVIEW:
        complaint.status = Complaint.StatusChoices.ASSIGNED
    
    complaint.save()

    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.ASSIGNMENT,
        previous_status=previous_status,
        new_status=complaint.status,
        note=f"Assigned to investigator {investigator.username}.",
        is_internal=True # Assignment notes are internal by default
    )
    
    return complaint


@transaction.atomic
def archive_complaint(complaint_id, actor):
    """
    Soft-deletes a complaint. Admin only. Preserves audit history.
    """
    if actor.role != 'ADMIN':
        raise PermissionDenied("Only administrators can archive complaints.")

    complaint = get_object_or_404(Complaint.objects.select_for_update(), id=complaint_id)
    
    if complaint.is_archived:
        raise ValidationError("Complaint is already archived.")

    complaint.is_archived = True
    complaint.save()

    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.ARCHIVED,
        note="Complaint archived by administrator.",
        is_internal=True
    )
    
    return complaint


@transaction.atomic
def add_internal_note(complaint_id, actor, note):
    """
    Allows Admins and assigned Investigators to add private internal notes.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if actor.role == 'ADMIN':
        pass
    elif actor.role == 'INVESTIGATOR' and complaint.assigned_investigator == actor:
        pass
    else:
        raise PermissionDenied("You do not have permission to add internal notes to this complaint.")

    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.NOTE,
        note=note,
        is_internal=True
    )
    
# complaints/services.py (Append at the bottom)

@transaction.atomic
def update_complaint(complaint_id, actor, title, description, category):
    """
    Allows a complainant to update their complaint if it's still pending review.
    """
    complaint = get_object_or_404(Complaint.objects.select_for_update(), id=complaint_id)

    # 1. Authorization
    if actor.role != 'COMPLAINANT' or complaint.complainant != actor:
        raise PermissionDenied("You can only edit your own complaints.")

    # 2. Status Check
    editable_statuses = [Complaint.StatusChoices.SUBMITTED, Complaint.StatusChoices.UNDER_REVIEW]
    if complaint.status not in editable_statuses:
        raise ValidationError("You cannot edit a complaint that is already under active investigation.")

    # 3. Apply Changes
    complaint.title = title
    complaint.description = description
    complaint.category = category
    complaint.save()

    # 4. Log Action
    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.UPDATE,
        note="Complainant updated the complaint details.",
        is_internal=False
    )
    return complaint


@transaction.atomic
def cancel_complaint(complaint_id, actor):
    """
    Allows a complainant to cancel (archive) their complaint.
    """
    complaint = get_object_or_404(Complaint.objects.select_for_update(), id=complaint_id)

    # 1. Authorization
    if actor.role != 'COMPLAINANT' or complaint.complainant != actor:
        raise PermissionDenied("You can only cancel your own complaints.")

    # 2. Status Check
    cancelable_statuses = [Complaint.StatusChoices.SUBMITTED, Complaint.StatusChoices.UNDER_REVIEW]
    if complaint.status not in cancelable_statuses:
        raise ValidationError("You cannot cancel a complaint that is already under active investigation.")

    # 3. Soft Delete (Archive)
    complaint.is_archived = True
    complaint.save()

    # 4. Log Action
    _create_activity_log(
        complaint=complaint,
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.ARCHIVED,
        note="Complainant cancelled/archived the complaint.",
        is_internal=False
    )
    return complaint