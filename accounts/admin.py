# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for Proofly's custom User model.

    Extends Django's built-in UserAdmin so that password hashing,
    permissions, groups, and the standard authentication workflow
    continue to work correctly.
    """

    model = User

    # Columns shown in the user list
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
    )

    # Filters shown on the right side of the user list
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
    )

    # Fields used when searching users
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    # Default ordering
    ordering = ("username",)

    # ------------------------------------------------------------------
    # "CHANGE USER" PAGE
    # ------------------------------------------------------------------
    # This controls the layout when an administrator edits an existing user.
    fieldsets = (
        (None, {
            "fields": (
                "username",
                "password",
            )
        }),
        (_("Personal info"), {
            "fields": (
                "first_name",
                "last_name",
                "email",
            )
        }),
        (_("Proofly role"), {
            "fields": ("role",),
            "description": (
                "Only authorized administrators should assign "
                "Investigator or Admin roles."
            ),
        }),
        (_("Permissions"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        (_("Important dates"), {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    # ------------------------------------------------------------------
    # "ADD USER" PAGE
    # ------------------------------------------------------------------
    # This controls the layout when an administrator creates a new user
    # directly from the Django admin.
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "role",
                "password1",
                "password2",
                "is_active",
                "is_staff",
            ),
        }),
    )

    # Read-only fields
    readonly_fields = ("last_login", "date_joined")