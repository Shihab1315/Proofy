# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

# ==========================================
# EXISTING AUTHENTICATION FORMS
# ==========================================

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': 'john@example.com'}))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': 'John'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': 'Doe'}),
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': 'johndoe'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': '••••••••'})
        self.fields['password2'].widget.attrs.update({'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': '••••••••'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = User.Role.COMPLAINANT 
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none', 'placeholder': '••••••••'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                    self.cleaned_data['username'] = username
                except User.DoesNotExist:
                    pass

        return super().clean()


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none'}),
            'bio': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none'}),
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file size must be under 2MB.")
            if not picture.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise forms.ValidationError("Only PNG and JPEG files are allowed.")
        return picture


# ==========================================
# NEW: INVESTIGATOR MANAGEMENT FORMS
# ==========================================

class InvestigatorCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Temporary Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': 'Enter a secure temporary password'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': 'Confirm the password'})
    )
    
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': '+880...'}))
    specialization = forms.ChoiceField(
        choices=Profile.SpecializationChoices.choices,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm bg-white'})
    )
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm resize-none', 'rows': 3, 'placeholder': 'Short professional bio...'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'block w-full text-sm text-[#475467] file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-[#10B981] hover:file:bg-emerald-100 transition-all cursor-pointer'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': 'John'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': 'Doe'}),
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': 'investigator_john'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm', 'placeholder': 'john@proofly.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data


class InvestigatorUpdateForm(forms.ModelForm):
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm'}))
    specialization = forms.ChoiceField(
        choices=Profile.SpecializationChoices.choices,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm bg-white'})
    )
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm resize-none', 'rows': 3}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'block w-full text-sm text-[#475467] file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-[#10B981] hover:file:bg-emerald-100 transition-all cursor-pointer'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm'}),
        }