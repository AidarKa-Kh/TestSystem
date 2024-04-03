from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import User


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_photo']


class ChangePasswordForm(PasswordChangeForm):
    pass
