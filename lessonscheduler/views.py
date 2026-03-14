from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from .forms import LessonCreateForm
from .models import Lesson

# Create your views here.


def index(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        account_type = "Teacher" if profile and profile.is_djteacher else "Student"
        upcoming_lessons = get_upcoming_lessons_for_user(request.user)
        return render(
            request,
            "user_homepage.html",
            {
                "account_type": account_type,
                "upcoming_lessons": upcoming_lessons,
            },
        )
    return render(request, "index.html")


def profile(request):
    return redirect('/users/profile/')


# Description: Phase 3/4 query helper and lesson views
# Generated with Copilot on March 14, 2026
# Prompt: lets work on phase 3 and 4 next
def get_upcoming_lessons_for_user(user):
    return (
        Lesson.objects.filter(
            Q(teacher=user) | Q(student=user),
            start_time__gte=timezone.now(),
        )
        .select_related("teacher", "student")
        .order_by("start_time")
    )


@login_required
def lesson_create(request):
    form = LessonCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("index")
    return render(request, "lesson_create.html", {"form": form})
