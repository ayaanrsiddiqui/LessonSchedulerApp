from django import forms
from .models import Profile

class ProfileUploadForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'intro_audio']


class ProfileBioForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell people a little about yourself...'
            })
        }
        