# accounts/services.py

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from complaints.models import ActivityLog

User = get_user_model()

def _log_system_event(actor, action_type, note, target_user):
    """Helper to log system-level admin actions."""
    ActivityLog.objects.create(
        complaint=None, # System level event
        actor=actor,
        actor_username=actor.username,
        actor_display_name=actor.get_full_name() or actor.username,
        action_type=action_type,
        note=note,
        is_internal=True # System logs are strictly for admins
    )

@transaction.atomic
def create_investigator(actor, form_data, profile_picture=None):
    """
    Creates a new Investigator securely.
    """
    if actor.role != 'ADMIN':
        raise PermissionDenied("Only admins can create investigator accounts.")

    # 1. Create User
    user = User.objects.create_user(
        username=form_data['username'],
        email=form_data['email'],
        password=form_data['password1'],
        first_name=form_data['first_name'],
        last_name=form_data['last_name'],
        role=User.Role.INVESTIGATOR,
        must_change_password=True # Force password change on first login
    )

    # 2. Update auto-created Profile
    profile = user.profile
    profile.specialization = form_data['specialization']
    profile.phone_number = form_data.get('phone_number', '')
    profile.bio = form_data.get('bio', '')
    if profile_picture:
        profile.profile_picture = profile_picture
    profile.save()

    # 3. Log Action
    _log_system_event(
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.INVESTIGATOR_CREATED,
        note=f"Created Investigator account: {user.username} ({user.get_full_name()})",
        target_user=user
    )

    return user

@transaction.atomic
def update_investigator(actor, investigator_id, form_data, profile_picture=None):
    """
    Updates an Investigator's profile details.
    """
    if actor.role != 'ADMIN':
        raise PermissionDenied("Only admins can edit investigator accounts.")

    investigator = get_object_or_404(User, id=investigator_id, role=User.Role.INVESTIGATOR)

    # Update User fields
    investigator.first_name = form_data['first_name']
    investigator.last_name = form_data['last_name']
    investigator.email = form_data['email']
    investigator.save()

    # Update Profile fields
    profile = investigator.profile
    profile.specialization = form_data['specialization']
    profile.phone_number = form_data.get('phone_number', '')
    profile.bio = form_data.get('bio', '')
    if profile_picture:
        profile.profile_picture = profile_picture
    profile.save()

    # Log Action
    _log_system_event(
        actor=actor,
        action_type=ActivityLog.ActionTypeChoices.INVESTIGATOR_UPDATED,
        note=f"Updated Investigator details for: {investigator.username}",
        target_user=investigator
    )

    return investigator

@transaction.atomic
def toggle_investigator_status(actor, investigator_id):
    """
    Activates or Deactivates an Investigator.
    """
    if actor.role != 'ADMIN':
        raise PermissionDenied("Only admins can change account status.")

    investigator = get_object_or_404(User, id=investigator_id, role=User.Role.INVESTIGATOR)
    
    # Toggle status
    investigator.is_active = not investigator.is_active
    investigator.save()

    action_type = (
        ActivityLog.ActionTypeChoices.INVESTIGATOR_ACTIVATED 
        if investigator.is_active else 
        ActivityLog.ActionTypeChoices.INVESTIGATOR_DEACTIVATED
    )
    
    status_text = "Activated" if investigator.is_active else "Deactivated"

    # Log Action
    _log_system_event(
        actor=actor,
        action_type=action_type,
        note=f"{status_text} Investigator account: {investigator.username}",
        target_user=investigator
    )

    return investigator