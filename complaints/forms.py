# complaints/forms.py

import os
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Complaint, Evidence

User = get_user_model()

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none text-sm',
                'placeholder': 'e.g., Unauthorized transaction on my account'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none text-sm resize-none',
                'placeholder': 'Please provide detailed information about the incident...',
                'rows': 5
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] focus:border-transparent transition-all outline-none text-sm bg-white appearance-none'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = "Complaint Title"
        self.fields['description'].label = "Detailed Description"
        self.fields['category'].label = "Complaint Category"
        self.fields['category'].choices = [('', 'Select a category...')] + list(self.fields['category'].choices)[1:]


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-[#475467] file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-[#10B981] hover:file:bg-emerald-100 transition-all cursor-pointer'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be under 10MB.")
            
            ext = os.path.splitext(file.name)[1].lower()
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            if ext not in valid_extensions:
                raise ValidationError("Only PDF, JPG, and PNG files are allowed.")
        return file


class AssignInvestigatorForm(forms.Form):
    investigator = forms.ModelChoiceField(
        queryset=User.objects.filter(role='INVESTIGATOR', is_active=True),
        empty_label="Select an investigator...",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm bg-white'
        })
    )


class StatusUpdateForm(forms.Form):
    new_status = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm bg-white'
        })
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm resize-none',
            'rows': 2,
            'placeholder': 'Optional note for this status change...'
        })
    )

    def __init__(self, *args, **kwargs):
        allowed_choices = kwargs.pop('allowed_choices', [])
        super().__init__(*args, **kwargs)
        self.fields['new_status'].choices = allowed_choices


class NoteForm(forms.Form):
    note = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-[#E5E7EB] focus:ring-2 focus:ring-[#10B981] outline-none text-sm resize-none',
            'rows': 3,
            'placeholder': 'Type your note here...'
        })
    )
    is_internal = forms.BooleanField(
        required=False,
        initial=True,
        label="Internal Note (Hidden from complainant)",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-[#10B981] bg-gray-100 border-gray-300 rounded focus:ring-[#10B981]'
        })
    )