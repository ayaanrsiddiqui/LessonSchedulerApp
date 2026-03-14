from django import forms
from .models import DJClass

class DJClassForm(forms.ModelForm):
    class Meta:
        model = DJClass
        fields = ['start_time', 'end_time', 'capacity', 'requirements', 'experience']