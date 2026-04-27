# Description: Forms for DJ class creation, student signup/request, and DJ request response
# Generated with Copilot on March 29, 2026
# Prompt: implement asymmetrical form workflow for DJs posting classes and students requesting/signing up

from django import forms
from django.contrib.auth.models import User
from typing import cast

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

    datetime_format = "%Y-%m-%d %H:%M"

    start_time = forms.DateTimeField(
        label="Start time",
        input_formats=[datetime_format],
        widget=forms.DateTimeInput(
            format=datetime_format,
            attrs={
                "class": "js-datetime",
                "autocomplete": "off",
                "placeholder": "YYYY-MM-DD HH:MM",
            },
        ),
    )
    end_time = forms.DateTimeField(
        label="End time",
        input_formats=[datetime_format],
        widget=forms.DateTimeInput(
            format=datetime_format,
            attrs={
                "class": "js-datetime",
                "autocomplete": "off",
                "placeholder": "YYYY-MM-DD HH:MM",
            },
        ),
    )

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

    dj = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="DJ",
        widget=forms.Select()
    )

    class Meta:
        model = ClassRequest
        fields = [
            "dj",
            "requested_start_time",
            "requested_end_time",
            "requested_skill_level",
            "requested_location",
            "requested_equipment",
            "description",
        ]
        widgets = {
            "requested_start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "requested_end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "requested_skill_level": forms.Select(choices=DIFFICULTY_CHOICES),
            "requested_location": forms.TextInput(attrs={"placeholder": "e.g., Studio A, Downtown"}),
            "requested_equipment": forms.Textarea(attrs={"rows": 3, "placeholder": "e.g., Controller, speakers, headphones"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Explain your request..."}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.instance.student = self.user

        dj_field = cast(forms.ModelChoiceField, self.fields["dj"])
        dj_field.queryset = User.objects.filter(profile__role__in=["teacher", "producer"]).order_by("first_name", "username")

        for field_name in self.fields:
            self.fields[field_name].required = True

    def save(self, commit=True):
        request_obj = super().save(commit=False)
        request_obj.student = self.user
        request_obj.dj = self.cleaned_data["dj"]
        if commit:
            request_obj.save()
        return request_obj


# DJ Form: Respond to requests
class ManageClassRequestForm(forms.ModelForm):
    """Form for DJs to accept or deny class requests."""

    status = forms.ChoiceField(
        choices=[
            ("accepted", "Accept"),
            ("denied", "Decline"),
        ],
        widget=forms.Select()
    )

    class Meta:
        model = ClassRequest
        fields = ["status"]

    def save(self, commit=True):
        request = super().save(commit=False)
        from django.utils import timezone
        request.responded_at = timezone.now()
        if commit:
            request.save()
        return request