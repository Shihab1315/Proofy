# accounts/decorators.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from functools import wraps
from django.contrib.auth import get_user_model

User = get_user_model()

def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has the required role.
    Raises 403 Forbidden if authenticated but unauthorized.
    Redirects to login if not authenticated.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Reusable shortcut decorators
def complainant_required(view_func):
    return role_required([User.Role.COMPLAINANT])(view_func)

def investigator_required(view_func):
    return role_required([User.Role.INVESTIGATOR])(view_func)

def admin_required(view_func):
    return role_required([User.Role.ADMIN])(view_func)