# Description: Role-aware scheduling views for integrated root dashboard, class browsing, signup, and request management
# Generated with Copilot on March 29, 2026
# Prompt: keep dashboard at root while supporting DJ/student workflows and request handling

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.db.models import Q, Count, F
from django.utils import timezone
from django.contrib import messages

from .forms import LessonCreateForm, ClassSignupForm, ClassRequestForm, ManageClassRequestForm
from .models import Lesson, ClassSignup, ClassRequest

# Create your views here.


def _render_dj_dashboard(request):
    posted_classes = Lesson.objects.filter(dj=request.user).order_by("-created_at")
    pending_requests = ClassRequest.objects.filter(
        dj=request.user, status="pending"
    ).order_by("-created_at")

    posted_classes = posted_classes.annotate(
        confirmed_count=Count("signups", filter=Q(signups__status="confirmed")),
        waitlisted_count=Count("signups", filter=Q(signups__status="waitlisted")),
    )

    return render(
        request,
        "user_homepage.html",
        {
            "account_type": "DJ",
            "is_dj": True,
            "posted_classes": posted_classes,
            "pending_requests": pending_requests,
        },
    )


def _render_student_dashboard(request):
    my_signups = ClassSignup.objects.filter(
        student=request.user, status="confirmed"
    ).select_related("lesson").order_by("lesson__start_time")

    return render(
        request,
        "user_homepage.html",
        {
            "account_type": "Student",
            "is_dj": False,
            "my_signups": my_signups,
        },
    )


def index(request):
    """Home page with integrated DJ/student dashboard for authenticated users."""
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        is_dj = profile and profile.is_djteacher
        if is_dj:
            return _render_dj_dashboard(request)
        return _render_student_dashboard(request)

    return render(request, "index.html")


def profile(request):
    return redirect('/users/profile/')


@login_required
def dj_dashboard(request):
    return redirect("index")


@login_required
def student_dashboard(request):
    return redirect("index")


@login_required
def lesson_create(request):
    """DJ: Create and post a new class."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.is_djteacher):
        raise Http404("Only DJs can post classes")
    
    form = LessonCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Class posted successfully!")
        return redirect("dj_dashboard")
    
    return render(request, "lesson_create.html", {"form": form})


@login_required
def dj_class_detail(request, lesson_id):
    """DJ: View class details and signup roster for one posted class."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.is_djteacher):
        raise Http404("Only DJs can view class details")

    lesson = get_object_or_404(Lesson, id=lesson_id, dj=request.user)

    signups = ClassSignup.objects.filter(lesson=lesson).select_related("student")
    confirmed_signups = signups.filter(status="confirmed").order_by("signed_up_at")
    waitlisted_signups = signups.filter(status="waitlisted").order_by("signed_up_at")

    return render(
        request,
        "lesson_detail.html",
        {
            "lesson": lesson,
            "confirmed_signups": confirmed_signups,
            "waitlisted_signups": waitlisted_signups,
        },
    )


@login_required
def browse_classes(request):
    """Student: Browse available classes."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.is_djteacher:
        raise Http404("Only students can browse classes")
    
    # Show all posted classes that still have available spots.
    available_classes = Lesson.objects.annotate(
        confirmed_count=Count('signups', filter=Q(signups__status='confirmed'))
    ).filter(
        dj__isnull=False,
        confirmed_count__lt=F('capacity')
    ).order_by("start_time").select_related("dj__profile")
    
    # Get classes student is already signed up for
    my_signups = ClassSignup.objects.filter(student=request.user).values_list('lesson_id', flat=True)
    
    return render(request, "browse_classes.html", {
        "available_classes": available_classes,
        "my_signup_ids": my_signups,
    })


@login_required
def class_signup(request, lesson_id):
    """Student: Sign up for a class."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.is_djteacher:
        raise Http404("Only students can sign up for classes")
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Check if already signed up
    if ClassSignup.objects.filter(student=request.user, lesson=lesson).exists():
        messages.warning(request, "You are already enrolled in this class!")
        return redirect("browse_classes")
    
    # Check if class is full
    confirmed_count = ClassSignup.objects.filter(
        lesson=lesson,
        status="confirmed",
    ).count()
    if confirmed_count >= lesson.capacity:
        messages.warning(request, "This class is full. You have been waitlisted.")
        status = "waitlisted"
    else:
        status = "confirmed"
    
    if request.method == "POST":
        form = ClassSignupForm(
            request.POST or None,
            user=request.user,
            lesson=lesson,
            status=status,
        )
        if form.is_valid():
            form.save()
            if status == "confirmed":
                messages.success(request, "Successfully signed up for the class!")
            else:
                messages.success(request, "Class is full. You have been added to the waitlist.")
            return redirect("index")
    else:
        form = ClassSignupForm(user=request.user, lesson=lesson, status=status)
    
    return render(request, "class_signup.html", {
        "lesson": lesson,
        "form": form,
        "will_be_waitlisted": status == "waitlisted",
    })


@login_required
def request_class(request, dj_id):
    """Student: Request a class at a specific date/time from a DJ."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.is_djteacher:
        raise Http404("Only students can request classes")
    
    dj_user = get_object_or_404(User, id=dj_id, profile__is_djteacher=True)
    
    form = ClassRequestForm(request.POST or None, user=request.user, dj=dj_user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Class request sent to {dj_user.get_full_name()}!")
        return redirect("browse_classes")
    
    return render(request, "request_class.html", {"dj": dj_user, "form": form})


@login_required
def manage_request(request, request_id):
    """DJ: Accept or deny a class request."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.is_djteacher):
        raise Http404("Only DJs can manage requests")
    
    class_request = get_object_or_404(ClassRequest, id=request_id, dj=request.user)
    
    form = ManageClassRequestForm(request.POST or None, instance=class_request)
    if request.method == "POST" and form.is_valid():
        form.save()
        status_text = "accepted" if class_request.status == "accepted" else "denied"
        messages.success(request, f"Request {status_text}!")
        return redirect("dj_dashboard")
    
    return render(request, "manage_request.html", {
        "class_request": class_request,
        "form": form,
    })
