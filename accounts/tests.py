# accounts/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import UserRegisterForm

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_url = reverse('accounts:profile')

        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='StrongPassword123!',
            role=User.Role.COMPLAINANT
        )
        self.investigator = User.objects.create_user(
            username='investigator', 
            email='investigator@example.com', 
            password='StrongPassword123!',
            role=User.Role.INVESTIGATOR
        )
        self.admin = User.objects.create_user(
            username='adminuser', 
            email='admin@example.com', 
            password='StrongPassword123!',
            role=User.Role.ADMIN
        )

    # 1. Registration Success
    def test_registration_success(self):
        response = self.client.post(self.register_url, {
            'first_name': 'New', 'last_name': 'User',
            'username': 'newuser', 'email': 'new@example.com',
            'password1': 'NewStrongPassword123!', 'password2': 'NewStrongPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # 2. Duplicate Username
    def test_duplicate_username(self):
        response = self.client.post(self.register_url, {
            'first_name': 'New', 'last_name': 'User',
            'username': 'testuser', 'email': 'another@example.com',
            'password1': 'NewStrongPassword123!', 'password2': 'NewStrongPassword123!'
        })
        self.assertEqual(response.status_code, 200) # Stays on page
        
        # Django 5.2-এর জন্য সঠিক সিনট্যাক্স:
        form = response.context['form']
        self.assertFormError(form, 'username', 'A user with that username already exists.')
    # 3. Duplicate Email
    def test_duplicate_email(self):
        form = UserRegisterForm(data={
            'first_name': 'New', 'last_name': 'User',
            'username': 'newuser2', 'email': 'test@example.com',
            'password1': 'NewStrongPassword123!', 'password2': 'NewStrongPassword123!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # 4. Password Mismatch
    def test_password_mismatch(self):
        form = UserRegisterForm(data={
            'first_name': 'New', 'last_name': 'User',
            'username': 'newuser3', 'email': 'new3@example.com',
            'password1': 'NewStrongPassword123!', 'password2': 'DifferentPassword123!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    # 5. Registration creates COMPLAINANT role
    def test_registration_always_complainant(self):
        self.client.post(self.register_url, {
            'first_name': 'New', 'last_name': 'User',
            'username': 'newuser4', 'email': 'new4@example.com',
            'password1': 'NewStrongPassword123!', 'password2': 'NewStrongPassword123!'
        })
        user = User.objects.get(username='newuser4')
        self.assertEqual(user.role, User.Role.COMPLAINANT)

    # 6. Attempted role escalation via POST
    def test_role_escalation_fails(self):
        self.client.post(self.register_url, {
            'first_name': 'Hacker', 'last_name': 'User',
            'username': 'hacker', 'email': 'hacker@example.com',
            'password1': 'NewStrongPassword123!', 'password2': 'NewStrongPassword123!',
            'role': 'ADMIN' # Malicious injection
        })
        user = User.objects.get(username='hacker')
        self.assertEqual(user.role, User.Role.COMPLAINANT) # Ignores the injected role

    # 7. Login with Username
    def test_login_with_username(self):
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'StrongPassword123!'})
        self.assertEqual(response.status_code, 302)

    # 8. Login with Email
    def test_login_with_email(self):
        response = self.client.post(self.login_url, {'username': 'test@example.com', 'password': 'StrongPassword123!'})
        self.assertEqual(response.status_code, 302)

    # 9. Invalid Login
    def test_invalid_login(self):
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'WrongPassword'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # 10. Logout via POST
    def test_logout(self):
        self.client.login(username='testuser', password='StrongPassword123!')
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # 11. Profile Update
    def test_profile_update(self):
        self.client.login(username='testuser', password='StrongPassword123!')
        response = self.client.post(reverse('accounts:edit_profile'), {
            'first_name': 'Updated', 'last_name': 'Name', 'email': 'test@example.com',
            'phone_number': '1234567890', 'bio': 'New bio'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.profile.phone_number, '1234567890')

    # 12. Cannot edit another user's profile (prevented by URL design - uses request.user)
    # URL is /profile/edit/ without an ID. So IDOR is physically impossible.

    # 13, 14, 15. Role based access
    def test_role_based_access(self):
        # Temporary view for testing decorators
        from .decorators import investigator_required, admin_required
        from django.http import HttpResponse
        from django.test import RequestFactory

        @investigator_required
        def dummy_investigator_view(request): return HttpResponse("OK")
        
        @admin_required
        def dummy_admin_view(request): return HttpResponse("OK")

        # Complainant tries investigator view
        self.client.login(username='testuser', password='StrongPassword123!')
        response = self.client.get(reverse('accounts:profile')) # using profile just as a proxy, or we can mock request
        
        # Testing decorator logic directly
        rf = RequestFactory()
        
        # Complainant -> investigator view (Forbidden)
        request = rf.get('/dummy/')
        request.user = self.user
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            dummy_investigator_view(request)

        # Investigator -> admin view (Forbidden)
        request.user = self.investigator
        with self.assertRaises(PermissionDenied):
            dummy_admin_view(request)

        # Admin -> admin view (Allowed)
        request.user = self.admin
        response = dummy_admin_view(request)
        self.assertEqual(response.status_code, 200)