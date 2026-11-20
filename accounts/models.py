# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    class Role(models.TextChoices):
        COMPLAINANT = "COMPLAINANT", "Complainant"
        INVESTIGATOR = "INVESTIGATOR", "Investigator"
        ADMIN = "ADMIN", "Admin"

    email = models.EmailField(unique=True, help_text="A unique email address is required.")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COMPLAINANT,
        help_text="Public registration always creates a Complainant account."
    )
    
    # NEW: Forces users (like new Investigators) to change their password on first login
    must_change_password = models.BooleanField(
        default=False,
        help_text="If true, the user must change their password on next login."
    )

    def clean(self):
        super().clean()
        if self.role not in self.Role.values:
            raise ValidationError({"role": "Invalid role selected."})

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["username"]


class Profile(models.Model):
    # NEW: Choices for Investigator Specialization
    class SpecializationChoices(models.TextChoices):
        CYBERCRIME = "CYBERCRIME", "Cybercrime"
        FRAUD = "FRAUD", "Financial Fraud"
        FORENSICS = "FORENSICS", "Digital Forensics"
        HARASSMENT = "HARASSMENT", "Harassment"
        GENERAL = "GENERAL", "General Investigation"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # NEW: Specialization field (Optional for Complainants, required for Investigators)
    specialization = models.CharField(
        max_length=50,
        choices=SpecializationChoices.choices,
        blank=True,
        null=True,
        help_text="Relevant only for Investigators."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Signals to automatically create or update Profile when a User is created/saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)