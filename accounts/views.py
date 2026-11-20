# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .forms import UserRegisterForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm, InvestigatorCreateForm, InvestigatorUpdateForm
from .decorators import admin_required
from complaints.models import Complaint
from . import services

User = get_user_model()

# --- PUBLIC VIEWS ---

def home_view(request):
    """
    Public landing page.
    """
    # Fetch active investigators
    investigators = User.objects.filter(
        role='INVESTIGATOR', 
        is_active=True
    ).select_related('profile').order_by('date_joined')[:4] # Get first 4 investigators
    
    context = {
        'investigators': investigators
    }
    return render(request, 'public/home.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home') # লগইন থাকলে হোম পেজে পাঠাবে

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                
                # STRICT REQUIREMENT: Always redirect to '/' after login.
                # The `next` parameter is intentionally ignored.
                return redirect('home')
            else:
                messages.error(request, "This account is inactive.")
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been securely logged out.")
    return redirect('home') # লগআউটের পর হোম পেজে পাঠাবে


@login_required
def force_password_change_view(request):
    """
    Forces users with must_change_password=True to update their password.
    """
    if not request.user.must_change_password:
        return redirect('home')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save()
            
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated successfully.")
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/force_password_change.html', {'form': form})


# --- PROFILE VIEWS ---

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/edit_profile.html', context)


# --- INVESTIGATOR MANAGEMENT VIEWS ---

@admin_required
def investigator_list_view(request):
    query = request.GET.get('q', '')
    investigators = User.objects.filter(role='INVESTIGATOR').annotate(
        active_cases=Count('assigned_complaints', filter=Q(assigned_complaints__status__in=['ASSIGNED', 'INVESTIGATING', 'ON_HOLD'])),
        total_cases=Count('assigned_complaints')
    ).order_by('-date_joined')

    if query:
        investigators = investigators.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(username__icontains=query) | 
            Q(email__icontains=query)
        )

    paginator = Paginator(investigators, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/investigator_list.html', {'page_obj': page_obj, 'query': query})


@admin_required
def investigator_create_view(request):
    if request.method == 'POST':
        form = InvestigatorCreateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                services.create_investigator(
                    actor=request.user, 
                    form_data=form.cleaned_data,
                    profile_picture=request.FILES.get('profile_picture')
                )
                messages.success(request, "Investigator created successfully.")
                return redirect('accounts:investigator_list')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = InvestigatorCreateForm()
    return render(request, 'accounts/investigator_form.html', {'form': form, 'action': 'Create'})


@admin_required
def investigator_detail_view(request, user_id):
    investigator = get_object_or_404(User, id=user_id, role='INVESTIGATOR')
    cases = Complaint.objects.filter(assigned_investigator=investigator).order_by('-created_at')
    
    active_cases = cases.filter(status__in=['ASSIGNED', 'INVESTIGATING', 'ON_HOLD']).count()
    resolved_cases = cases.filter(status__in=['RESOLVED', 'CLOSED']).count()

    context = {
        'investigator': investigator,
        'cases': cases,
        'active_cases': active_cases,
        'resolved_cases': resolved_cases,
        'total_cases': cases.count()
    }
    return render(request, 'accounts/investigator_detail.html', context)


@admin_required
def investigator_edit_view(request, user_id):
    investigator = get_object_or_404(User, id=user_id, role='INVESTIGATOR')
    
    if request.method == 'POST':
        form = InvestigatorUpdateForm(request.POST, request.FILES, instance=investigator)
        if form.is_valid():
            try:
                services.update_investigator(
                    actor=request.user, 
                    investigator_id=investigator.id,
                    form_data=form.cleaned_data,
                    profile_picture=request.FILES.get('profile_picture')
                )
                messages.success(request, "Investigator updated successfully.")
                return redirect('accounts:investigator_detail', user_id=investigator.id)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = InvestigatorUpdateForm(instance=investigator, initial={
            'phone_number': investigator.profile.phone_number,
            'specialization': investigator.profile.specialization,
            'bio': investigator.profile.bio,
            'profile_picture': investigator.profile.profile_picture
        })
    
    return render(request, 'accounts/investigator_form.html', {'form': form, 'action': 'Edit', 'investigator': investigator})


@admin_required
@require_POST
def investigator_toggle_status_view(request, user_id):
    try:
        investigator = services.toggle_investigator_status(actor=request.user, investigator_id=user_id)
        status = "activated" if investigator.is_active else "deactivated"
        messages.success(request, f"Investigator {status} successfully.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('accounts:investigator_list')