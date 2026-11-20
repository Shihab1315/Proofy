# dashboard/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from complaints.models import Complaint
from django.db.models import Count
from django.db.models.functions import TruncMonth
from accounts.models import User

@login_required
def dashboard_redirect(request):
    """
    Intelligent redirect based on user role.
    """
    # রোলের নাম যাতে ছোট/বড় হাতের অক্ষরের কারণে ভুল না হয়, তাই .upper() ব্যবহার করা হলো
    role = str(request.user.role).upper() if request.user.role else ""
    
    if role == 'ADMIN' or request.user.is_superuser:
        return redirect('dashboard:admin')
    elif role == 'INVESTIGATOR':
        return redirect('dashboard:investigator')
    else:
        return redirect('dashboard:complainant')


@login_required
def complainant_dashboard(request):
    if request.user.role != 'COMPLAINANT':
        raise PermissionDenied("Access restricted to complainants.")
        
    complaints = Complaint.active_objects.filter(complainant=request.user).order_by('-created_at')
    
    total = complaints.count()
    pending = complaints.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).count()
    investigating = complaints.filter(status__in=['ASSIGNED', 'INVESTIGATING', 'ON_HOLD']).count()
    resolved = complaints.filter(status__in=['RESOLVED', 'CLOSED']).count()

    # Get recent activity logs for the user's complaints
    from complaints.models import ActivityLog
    recent_activity = ActivityLog.objects.filter(
        complaint__in=complaints, 
        is_internal=False
    ).order_by('-created_at')[:5]

    context = {
        'total': total, 
        'pending': pending, 
        'investigating': investigating, 
        'resolved': resolved,
        'recent_complaints': complaints[:5],
        'recent_activity': recent_activity,
    }
    return render(request, 'dashboard/complainant_dashboard.html', context)


@login_required
def investigator_dashboard(request):
    if request.user.role != 'INVESTIGATOR':
        raise PermissionDenied("Access restricted to investigators.")
        
    cases = Complaint.active_objects.filter(assigned_investigator=request.user).order_by('-updated_at')
    
    total = cases.count()
    pending = cases.filter(status='ASSIGNED').count()
    investigating = cases.filter(status='INVESTIGATING').count()
    on_hold = cases.filter(status='ON_HOLD').count()
    resolved = cases.filter(status='RESOLVED').count()

    # Get high priority cases for the table
    priority_cases = cases.filter(
        priority__in=['HIGH', 'URGENT'], 
        status__in=['ASSIGNED', 'INVESTIGATING', 'ON_HOLD']
    ).order_by('-created_at')[:5]

    context = {
        'total': total, 
        'pending': pending, 
        'investigating': investigating, 
        'on_hold': on_hold,
        'resolved': resolved,
        'recent_cases': cases[:10],
        'priority_cases': priority_cases,
    }
    return render(request, 'dashboard/investigator_dashboard.html', context)


# --- এই ভিউটি আগে মিসিং ছিল, যা এখন যুক্ত করা হলো ---
@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        raise PermissionDenied("Access restricted to administrators.")
        
    complaints = Complaint.active_objects.all()
    users = User.objects.all()
    
    # 1. Basic Stats
    total_complaints = complaints.count()
    total_investigators = users.filter(role='INVESTIGATOR').count()
    pending_complaints = complaints.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).count()
    active_investigations = complaints.filter(status__in=['ASSIGNED', 'INVESTIGATING', 'ON_HOLD']).count()
    resolved_complaints = complaints.filter(status__in=['RESOLVED', 'CLOSED']).count()

    # 2. Chart Data: Status Distribution (Doughnut Chart)
    status_counts = complaints.values('status').annotate(count=Count('id'))
    status_labels = []
    status_data = []
    for item in status_counts:
        # Get the display name for the status choice
        status_labels.append(dict(Complaint.StatusChoices.choices).get(item['status'], item['status']))
        status_data.append(item['count'])

    # 3. Chart Data: Monthly Trends (Line Chart)
    monthly_trends = complaints.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
    trend_labels = [item['month'].strftime("%b %Y") for item in monthly_trends if item['month']]
    trend_data = [item['count'] for item in monthly_trends if item['month']]

    # 4. Chart Data: Category Distribution (Bar Chart)
    category_counts = complaints.values('category').annotate(count=Count('id'))
    category_labels = []
    category_data = []
    for item in category_counts:
        category_labels.append(dict(Complaint.CategoryChoices.choices).get(item['category'], item['category']))
        category_data.append(item['count'])

    context = {
        'total_complaints': total_complaints,
        'total_investigators': total_investigators,
        'pending_complaints': pending_complaints,
        'active_investigations': active_investigations,
        'resolved_complaints': resolved_complaints,
        'recent_complaints': complaints.order_by('-created_at')[:5],
        
        # Pass JSON data to template
        'status_labels': status_labels,
        'status_data': status_data,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'category_labels': category_labels,
        'category_data': category_data,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)