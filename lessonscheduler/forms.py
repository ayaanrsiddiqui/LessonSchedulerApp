# Description: Forms for DJ class creation, student signup/request, and DJ request response
# Generated with Copilot on March 29, 2026
# Prompt: implement asymmetrical form workflow for DJs posting classes and students requesting/signing up

from django import forms
from django.contrib.auth.models import User

from .models import Lesson, ClassSignup, ClassRequest


DIFFICULTY_CHOICES = [
    ("Beginner", "Beginner"),
    ("Intermediate", "Intermediate"),
    ("Proficient", "Proficient"),
    ("Advanced", "Advanced"),
]


# DJ Form: Create or edit a class
class LessonForm(forms.ModelForm):
    """Form for DJs to create and edit classes."""

    experience_requirements = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        label="Skill Level",
        widget=forms.Select()
    )

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "image",
            "location",
            "capacity",
            "experience_requirements",
            "start_time",
            "end_time",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g., 'House Music Basics'"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe your class..."}),
            "image": forms.ClearableFileInput(),
            "location": forms.TextInput(attrs={"placeholder": "e.g., 'Studio A, Downtown'"}),
            "capacity": forms.NumberInput(attrs={"min": 1}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].required = True
        
        self.fields["image"].required = False

    def save(self, commit=True):
        lesson = super().save(commit=False)
        lesson.dj = self.user
        if commit:
            lesson.save()
        return lesson


# Student Form: Sign up for a class
class ClassSignupForm(forms.ModelForm):
    """Form for students to sign up for a posted class."""

    class Meta:
        model = ClassSignup
        fields = []

    def __init__(self, *args, user, lesson, status="confirmed", **kwargs):
        self.user = user
        self.lesson = lesson
        self.status = status
        super().__init__(*args, **kwargs)

        self.instance.student = self.user
        self.instance.lesson = self.lesson
        self.instance.status = self.status

    def save(self, commit=True):
        signup = super().save(commit=False)
        signup.student = self.user
        signup.lesson = self.lesson
        signup.status = self.status
        if commit:
            signup.save()
        return signup


# Student Form: Request a class
class ClassRequestForm(forms.ModelForm):
    """Form for students to request a specific date/time from a DJ."""

    class Meta:
        model = ClassRequest
        fields = ["requested_start_time", "requested_end_time", "description"]
        widgets = {
            "requested_start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "requested_end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Explain why you need this specific time..."}),
        }

    def __init__(self, *args, user, dj, **kwargs):
        self.user = user
        self.dj = dj
        super().__init__(*args, **kwargs)
        self.fields["requested_start_time"].required = True
        self.fields["requested_end_time"].required = True
        self.fields["description"].required = True

    def save(self, commit=True):
        request = super().save(commit=False)
        request.student = self.user
        request.dj = self.dj
        if commit:
            request.save()
        return request


# DJ Form: Respond to requests
class ManageClassRequestForm(forms.ModelForm):
    """Form for DJs to accept or deny class requests."""

    class Meta:
        model = ClassRequest
        fields = ["status"]
        widgets = {
            "status": forms.Select(choices=[
                ("pending", "Pending"),
                ("accepted", "Accept Request"),
                ("denied", "Deny Request"),
            ])
        }

    def save(self, commit=True):
        request = super().save(commit=False)
        from django.utils import timezone
        request.responded_at = timezone.now()
        if commit:
            request.save()
        return request