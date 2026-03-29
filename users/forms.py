from django import forms
from .models import Profile

class ProfileUploadForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'intro_audio']
        