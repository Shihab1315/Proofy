# complaints/admin.py

from django.contrib import admin
from .models import Complaint, ActivityLog

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_id', 'title', 'category', 'status', 
        'priority', 'complainant', 'assigned_investigator', 'created_at'
    )
    list_filter = ('status', 'priority', 'category', 'is_archived')
    search_fields = (
        'tracking_id', 'title', 'description', 
        'complainant__username', 'assigned_investigator__username'
    )
    readonly_fields = ('tracking_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Complaint Details', {
            'fields': ('tracking_id', 'title', 'description', 'category')
        }),
        ('Status & Management', {
            'fields': ('status', 'priority', 'assigned_investigator', 'is_archived')
        }),
        ('Ownership & Timestamps', {
            'fields': ('complainant', 'created_at', 'updated_at')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent hard deletion of complaints to preserve audit history
        return False


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        'complaint', 'actor_username', 'action_type', 
        'previous_status', 'new_status', 'is_internal', 'created_at'
    )
    list_filter = ('action_type', 'is_internal', 'created_at')
    search_fields = ('complaint__tracking_id', 'actor_username', 'note')
    
    # Force Read-Only
    readonly_fields = (
        'complaint', 'actor', 'actor_username', 'actor_display_name',
        'action_type', 'previous_status', 'new_status', 'note', 
        'is_internal', 'created_at'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False