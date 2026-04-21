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

from .forms import LessonForm, ClassSignupForm, ClassRequestForm, ManageClassRequestForm
from .models import Lesson, ClassSignup, ClassRequest
from messaging.models import Message as DirectMessage
from users.decorators import block_user_admin

# Create your views here.


def _format_lesson_update_value(field_name, value):
    if field_name in {"start_time", "end_time"} and value:
        return timezone.localtime(value).strftime("%b %d, %Y %H:%M")

    if field_name == "image_name":
        if not value:
            return "No image"
        return value.rsplit("/", 1)[-1]

    if value in (None, ""):
        return "None"

    return str(value)


def _build_lesson_update_notification(lesson, previous_state):
    tracked_fields = [
        ("title", "title", "Title"),
        ("description", "description", "Description"),
        ("location", "location", "Location"),
        ("capacity", "capacity", "Capacity"),
        ("experience_requirements", "experience_requirements", "Experience requirements"),
        ("start_time", "start_time", "Start time"),
        ("end_time", "end_time", "End time"),
        ("image_name", "image", "Image"),
    ]

    change_lines = []

    for previous_key, current_attr, label in tracked_fields:
        if current_attr == "image":
            current_value = lesson.image.name if lesson.image else ""
        else:
            current_value = getattr(lesson, current_attr)

        previous_value = previous_state[previous_key]

        if previous_value != current_value:
            change_lines.append(
                f"- {label}\n"
                f"  Before: {_format_lesson_update_value(previous_key, previous_value)}\n"
                f"  After: {_format_lesson_update_value(previous_key, current_value)}"
            )

    if not change_lines:
        return None

    start_display = timezone.localtime(lesson.start_time).strftime("%b %d, %Y %H:%M")
    end_display = timezone.localtime(lesson.end_time).strftime("%H:%M")

    return (
        f"[Automated Message] The class '{lesson.title}' was updated.\n\n"
        f"What changed:\n"
        f"{chr(10).join(change_lines)}\n\n"
        f"Current class details:\n"
        f"- Schedule: {start_display} - {end_display}\n"
        f"- Location: {lesson.location}\n"
        f"- Capacity: {lesson.capacity}\n"
        f"- Skill level: {lesson.experience_requirements}"
    )


def _serialize_calendar_lessons(lessons, is_dj):
    serialized = []
    for lesson in lessons:
        start_local = timezone.localtime(lesson.start_time)
        end_local = timezone.localtime(lesson.end_time)

        if is_dj:
            confirmed_count = ClassSignup.objects.filter(
                lesson=lesson,
                status="confirmed",
            ).count()
            role_line = f"Confirmed: {confirmed_count}/{lesson.capacity}"
        else:
            role_line = f"DJ: {lesson.dj.get_full_name() or lesson.dj.username}"

        serialized.append(
            {
                "date_key": start_local.date().isoformat(),
                "title": lesson.title,
                "start_display": start_local.strftime("%b %d, %Y %H:%M"),
                "end_display": end_local.strftime("%H:%M"),
                "location": lesson.location,
                "role_line": role_line,
            }
        )
    return serialized


def _render_dj_dashboard(request):
    today = timezone.localdate()

    posted_classes = Lesson.objects.filter(
        dj=request.user,
        start_time__date__gte=today,
    ).order_by("start_time")

    pending_requests = ClassRequest.objects.filter(
        dj=request.user, status="pending"
    ).order_by("-created_at")

    posted_classes = posted_classes.annotate(
        confirmed_count=Count("signups", filter=Q(signups__status="confirmed")),
        waitlisted_count=Count("signups", filter=Q(signups__status="waitlisted")),
    )
    calendar_lessons = _serialize_calendar_lessons(posted_classes, is_dj=True)

    return render(
        request,
        "user_homepage.html",
        {
            "account_type": "DJ",
            "is_dj": True,
            "posted_classes": posted_classes,
            "pending_requests": pending_requests,
            "calendar_lessons": calendar_lessons,
        },
    )


def _render_student_dashboard(request):
    today = timezone.localdate()

    available_lessons = Lesson.objects.filter(
        start_time__date__gte=today
    ).select_related("dj").order_by("start_time")

    confirmed_signup_ids = set(
        ClassSignup.objects.filter(
            student=request.user,
            status="confirmed",
        ).values_list("lesson_id", flat=True)
    )

    waitlisted_signup_ids = set(
        ClassSignup.objects.filter(
            student=request.user,
            status="waitlisted",
        ).values_list("lesson_id", flat=True)
    )

    calendar_lessons = _serialize_calendar_lessons(
        available_lessons,
        is_dj=False,
    )

    return render(
        request,
        "user_homepage.html",
        {
            "account_type": "Student",
            "is_dj": False,
            "available_lessons": available_lessons,
            "confirmed_signup_ids": confirmed_signup_ids,
            "waitlisted_signup_ids": waitlisted_signup_ids,
            "calendar_lessons": calendar_lessons,
        },
    )

@block_user_admin
def index(request):
    """Home page with integrated DJ/student dashboard for authenticated users."""
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        is_dj = profile and profile.role == "teacher"
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
@block_user_admin
def lesson_create(request):
    """DJ: Create and post a new class."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.role == "teacher"):
        raise Http404("Only DJs can post classes")

    request_id = request.GET.get("request_id")
    initial = {}
    source_request = None

    if request_id:
        source_request = get_object_or_404(
            ClassRequest,
            id=request_id,
            dj=request.user,
            status="accepted",
            request_type="new",
        )
        initial = {
            "location": source_request.requested_location,
            "experience_requirements": source_request.requested_skill_level,
            "start_time": timezone.localtime(source_request.requested_start_time).strftime("%Y-%m-%dT%H:%M"),
            "end_time": timezone.localtime(source_request.requested_end_time).strftime("%Y-%m-%dT%H:%M"),
            "description": (
                f"{source_request.description}\n\nRequested equipment: {source_request.requested_equipment}"
            ),
        }

    form = LessonForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        initial=initial if request.method == "GET" else None,
    )

    if request.method == "POST" and form.is_valid():
        lesson = form.save()

        if source_request:
            DirectMessage.objects.create(
                sender=request.user,
                recipient=source_request.student,
                content=(
                    f"[Automated Message] Your accepted class request has now been scheduled as '{lesson.title}' "
                    f"for {timezone.localtime(lesson.start_time).strftime('%b %d, %Y %H:%M')} - "
                    f"{timezone.localtime(lesson.end_time).strftime('%H:%M')} at {lesson.location}."
                ),
            )

        messages.success(request, "Class posted successfully!")
        return redirect("dj_dashboard")

    return render(request, "lesson_create.html", {"form": form})

@login_required
@block_user_admin
def lesson_edit(request, lesson_id):
    """DJ: Edit details for one posted class."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.role == "teacher"):
        raise Http404("Only DJs can edit classes")

    lesson = get_object_or_404(Lesson, id=lesson_id, dj=request.user)

     #delete button right here
    if request.method == "POST" and "delete" in request.POST:
        lesson.delete()
        messages.success(request, "Class deleted successfully!")
        return redirect("dj_dashboard")

    
    if lesson.start_time.date() < timezone.localdate() and request.method != "POST":
        messages.error(request, "Past classes can no longer be edited.")
        return redirect("dj_class_detail", lesson_id=lesson.pk)
    
    previous_state = {
        "title": lesson.title,
        "description": lesson.description,
        "location": lesson.location,
        "capacity": lesson.capacity,
        "experience_requirements": lesson.experience_requirements,
        "start_time": lesson.start_time,
        "end_time": lesson.end_time,
        "image_name": lesson.image.name if lesson.image else "",
    }

    request_id = request.GET.get("request_id")
    source_request = None

    if request_id:
        source_request = get_object_or_404(
            ClassRequest,
            id=request_id,
            dj=request.user,
            lesson=lesson,
            status="accepted",
            request_type="edit",
        )

    form_initial = None
    if request.method == "GET" and source_request:
        form_initial = {
            "location": source_request.requested_location or lesson.location,
            "experience_requirements": source_request.requested_skill_level or lesson.experience_requirements,
            "start_time": timezone.localtime(source_request.requested_start_time).strftime("%Y-%m-%dT%H:%M"),
            "end_time": timezone.localtime(source_request.requested_end_time).strftime("%Y-%m-%dT%H:%M"),
            "description": (
                f"{source_request.description}\n\nRequested equipment: {source_request.requested_equipment}"
            ),
        }

    form = LessonForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        instance=lesson,
        initial=form_initial,
    )

    if request.method == "POST" and "delete" not in request.POST and form.is_valid():
        updated_lesson = form.save()

        if source_request:
            DirectMessage.objects.create(
                sender=request.user,
                recipient=source_request.student,
                content=(
                    f"[Automated Message] Your accepted request to update '{updated_lesson.title}' has been applied. "
                    f"New schedule: {timezone.localtime(updated_lesson.start_time).strftime('%b %d, %Y %H:%M')} - "
                    f"{timezone.localtime(updated_lesson.end_time).strftime('%H:%M')} at {updated_lesson.location}."
                ),
            )

        changed_labels = []
        tracked_fields = [
            ("title", "title"),
            ("description", "description"),
            ("location", "location"),
            ("capacity", "capacity"),
            ("experience_requirements", "experience requirements"),
            ("start_time", "start time"),
            ("end_time", "end time"),
        ]

        for field_name, label in tracked_fields:
            if previous_state[field_name] != getattr(updated_lesson, field_name):
                changed_labels.append(label)

        updated_image_name = updated_lesson.image.name if updated_lesson.image else ""
        if previous_state["image_name"] != updated_image_name:
            changed_labels.append("image")

        if changed_labels:
            signed_up_students = User.objects.filter(
                class_signups__lesson=updated_lesson,
                class_signups__status__in=["confirmed", "waitlisted"],
            ).distinct()

            notification_text = _build_lesson_update_notification(updated_lesson, previous_state)

            notified_count = 0
            if notification_text:
                for student in signed_up_students:
                    DirectMessage.objects.create(
                        sender=request.user,
                        recipient=student,
                        content=notification_text,
                    )
                    notified_count += 1

            if notified_count:
                messages.info(request, f"Notified {notified_count} signed-up student(s) about this update.")

        messages.success(request, "Class updated successfully!")
        return redirect("dj_class_detail", lesson_id=lesson.pk)

    return render(
        request,
        "lesson_edit.html",
        {"form": form, "lesson": lesson},
    )


@login_required
@block_user_admin
def dj_class_detail(request, lesson_id):
    """DJ: View class details and signup roster for one posted class."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.role == "teacher"):
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
            "can_edit_lesson": lesson.start_time.date() >= timezone.localdate(),
        },
    )

@login_required
@block_user_admin
def student_class_detail(request, lesson_id):
    """Student: View class details for a lesson."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "teacher":
        raise Http404("Only students can view student class details")

    lesson = get_object_or_404(Lesson, id=lesson_id)

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
            "can_edit_lesson": False,
            "is_student_view": True,
        },
    )


@login_required
@block_user_admin
def browse_classes(request):
    """Student: Browse available classes."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "teacher":
        raise Http404("Only students can browse classes")

    today = timezone.localdate()

    available_classes = Lesson.objects.annotate(
        confirmed_count=Count('signups', filter=Q(signups__status='confirmed'))
    ).filter(
        dj__isnull=False,
        start_time__date__gte=today,
        confirmed_count__lt=F('capacity')
    ).order_by("start_time").select_related("dj__profile")

    confirmed_signup_ids = set(
        ClassSignup.objects.filter(
            student=request.user,
            status="confirmed",
        ).values_list("lesson_id", flat=True)
    )

    waitlisted_signup_ids = set(
        ClassSignup.objects.filter(
            student=request.user,
            status="waitlisted",
        ).values_list("lesson_id", flat=True)
    )

    return render(request, "browse_classes.html", {
        "available_classes": available_classes,
        "confirmed_signup_ids": confirmed_signup_ids,
        "waitlisted_signup_ids": waitlisted_signup_ids,
    })


@login_required
@block_user_admin
def class_signup(request, lesson_id):
    """Student: Sign up for a class."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "teacher":
        raise Http404("Only students can sign up for classes")

    lesson = get_object_or_404(Lesson, id=lesson_id)

    # If user clicked on signup from home page or browse page it stays there, god willing
    redirect_target = request.POST.get("next") or request.GET.get("next") or "index"

    # Check if already signed up in an active status
    existing_signup = ClassSignup.objects.filter(
        student=request.user,
        lesson=lesson,
        status__in=["confirmed", "waitlisted"],
    ).first()
    if existing_signup:
        messages.warning(request, "You are already enrolled in this class!")
        return redirect(redirect_target)

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
        # If student cancelled before and is signing up again, reactivate that row
        cancelled_signup = ClassSignup.objects.filter(
            student=request.user,
            lesson=lesson,
            status="cancelled",
        ).first()

        if cancelled_signup:
            cancelled_signup.status = status
            cancelled_signup.save()
        else:
            form = ClassSignupForm(
                request.POST or None,
                user=request.user,
                lesson=lesson,
                status=status,
            )
            if form.is_valid():
                form.save()
            else:
                messages.error(request, "Could not sign up for this class.")
                return redirect(redirect_target)

        if status == "confirmed":
            messages.success(request, "Successfully signed up for the class!")
        else:
            messages.success(request, "Class is full. You have been added to the waitlist.")
        return redirect(redirect_target)

    # Keep the old confirmation page only if someone visits the URL directly
    form = ClassSignupForm(user=request.user, lesson=lesson, status=status)
    return render(request, "class_signup.html", {
        "lesson": lesson,
        "form": form,
        "will_be_waitlisted": status == "waitlisted",
    })


@login_required
@block_user_admin
def request_class(request):
    """Student: Request a class, optionally prefilled from an existing lesson."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "teacher":
        raise Http404("Only students can request classes")

    lesson_id = request.GET.get("lesson_id") or request.POST.get("lesson_id")
    lesson = None
    initial = {}
    next_target = request.GET.get("next") or request.POST.get("next") or "browse_classes"

    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        initial = {
            "dj": lesson.dj,
            "requested_start_time": timezone.localtime(lesson.start_time).strftime("%Y-%m-%dT%H:%M"),
            "requested_end_time": timezone.localtime(lesson.end_time).strftime("%Y-%m-%dT%H:%M"),
            "requested_skill_level": lesson.experience_requirements,
            "requested_location": lesson.location,
            "requested_equipment": "",
            "description": f"I'd like to request changes to '{lesson.title}'.",
        }

    form = ClassRequestForm(
        request.POST or None,
        user=request.user,
        initial=initial if request.method == "GET" else None,
    )

    if request.method == "POST" and form.is_valid():
        class_request = form.save(commit=False)
        class_request.lesson = lesson
        class_request.request_type = "edit" if lesson else "new"
        class_request.save()

        messages.success(
            request,
            f"Class request sent to {class_request.dj.get_full_name() or class_request.dj.username}!"
        )
        return redirect(next_target)

    return render(
        request,
        "request_class.html",
        {
            "form": form,
            "next_target": next_target,
            "prefill_lesson_id": lesson_id,
            "prefill_lesson": lesson,
        },
    )

@login_required
@block_user_admin
def manage_request(request, request_id):
    """DJ: Accept or deny a class request."""
    profile = getattr(request.user, "profile", None)
    if not (profile and profile.role == "teacher"):
        raise Http404("Only DJs can manage requests")

    class_request = get_object_or_404(ClassRequest, id=request_id, dj=request.user)
    form = ManageClassRequestForm(request.POST or None, instance=class_request)

    if request.method == "POST" and form.is_valid():
        updated_request = form.save()

        student = updated_request.student
        start_display = timezone.localtime(updated_request.requested_start_time).strftime("%b %d, %Y %H:%M")
        end_display = timezone.localtime(updated_request.requested_end_time).strftime("%H:%M")

        if updated_request.status == "accepted":
            if updated_request.request_type == "edit" and updated_request.lesson:
                DirectMessage.objects.create(
                    sender=request.user,
                    recipient=student,
                    content=(
                        f"[Automated Message] Your request to update '{updated_request.lesson.title}' was accepted. "
                        f"The DJ is now reviewing your requested changes for {start_display} - {end_display} at "
                        f"{updated_request.requested_location or updated_request.lesson.location}."
                    ),
                )

                messages.success(request, "Request accepted! You can now update the class.")
                return redirect(
                    f"{redirect('lesson_edit', lesson_id=updated_request.lesson.id).url}"
                    f"?request_id={updated_request.id}"
                )

            DirectMessage.objects.create(
                sender=request.user,
                recipient=student,
                content=(
                    f"[Automated Message] Your class request was accepted. "
                    f"The DJ is now creating your requested class for {start_display} - {end_display} at "
                    f"{updated_request.requested_location}."
                ),
            )

            messages.success(request, "Request accepted! You can now create the class.")
            return redirect(f"{redirect('lesson_create').url}?request_id={updated_request.id}")

        DirectMessage.objects.create(
            sender=request.user,
            recipient=student,
            content=(
                f"[Automated Message] Your class request was denied. "
                f"Requested time was {start_display} - {end_display}."
            ),
        )

        messages.success(request, "Request denied.")
        return redirect("dj_dashboard")

    return render(request, "manage_request.html", {
        "class_request": class_request,
        "form": form,
    })

def cancel_booking(request, lesson_id):
    """Student: Cancel a booked class."""
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "teacher":
        raise Http404("Only students can cancel bookings")

    signup = get_object_or_404(
        ClassSignup,
        student=request.user,
        lesson_id=lesson_id,
        status__in=["confirmed", "waitlisted"],
    )

    redirect_target = request.POST.get("next") or "index"

    if request.method == "POST":
        signup.status = "cancelled"
        signup.save()
        messages.success(request, "Booking cancelled successfully.")

    return redirect(redirect_target)
