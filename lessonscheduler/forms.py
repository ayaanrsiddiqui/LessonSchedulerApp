from django import forms
from django.contrib.auth.models import User

from .models import Lesson


# Description: Lesson creation form with role-aware teacher/student assignment
# Generated with Copilot on March 14, 2026
# Prompt: lets work on phase 3 and 4 next
class LessonCreateForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "description", "start_time", "end_time"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["start_time"].required = True
        self.fields["end_time"].required = True

        if self.user.profile.is_djteacher:
            self.fields["student"] = forms.ModelChoiceField(
                queryset=User.objects.filter(profile__is_djteacher=False).exclude(
                    pk=self.user.pk
                ),
                required=True,
            )
        else:
            self.fields["teacher"] = forms.ModelChoiceField(
                queryset=User.objects.filter(profile__is_djteacher=True).exclude(
                    pk=self.user.pk
                ),
                required=True,
            )

    def save(self, commit=True):
        lesson = super().save(commit=False)

        if self.user.profile.is_djteacher:
            lesson.teacher = self.user
            lesson.student = self.cleaned_data["student"]
        else:
            lesson.student = self.user
            lesson.teacher = self.cleaned_data["teacher"]

        if commit:
            lesson.save()

        return lesson