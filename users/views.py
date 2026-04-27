from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import ProfileBioForm
from .models import Profile, RoleChangeRequest
from .decorators import block_user_admin, admin_only


@login_required
@block_user_admin
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        bio_form = ProfileBioForm(request.POST, instance=profile)
        if bio_form.is_valid():
            bio_form.save()
            return redirect('profile')
    else:
        bio_form = ProfileBioForm(instance=profile)

    pending_teacher_request = RoleChangeRequest.objects.filter(
        profile=profile,
        status="pending",
        requested_role="teacher",
    ).first() if profile.role == 'student' else None

    return render(request, "users/profile.html", {
        "profile": profile,
        "bio_form": bio_form,
        "pending_teacher_request": pending_teacher_request,
    })


@login_required
def public_profile_view(request, username):
    profile = get_object_or_404(Profile.objects.select_related("user"), user__username=username)

    return render(request, "users/public_profile.html", {
        "profile": profile,
        "viewed_user": profile.user,
        "is_own_profile": profile.user == request.user,
    })

# Profile Picture and Audio upload
@login_required
@block_user_admin
def upload_profile_files(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Handle removals first
        if 'remove_profile_picture' in request.POST and profile.profile_picture:
            profile.profile_picture.delete()
        if 'remove_intro_audio' in request.POST and profile.intro_audio:
            profile.intro_audio.delete()

        # Handle new uploads
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        if 'intro_audio' in request.FILES:
            profile.intro_audio = request.FILES['intro_audio']

        profile.save()
        return redirect('profile')

    return render(request, 'users/upload_files.html', {'profile': profile})

# Admin view to manage user roles
@login_required
@admin_only
def manage_roles(request):

    users = Profile.objects.exclude(role="admin_user")
    pending_requests = RoleChangeRequest.objects.filter(status="pending").select_related("profile__user").order_by("submitted_at")

    return render(request, "users/manage_roles.html", {
        "users": users,
        "pending_requests": pending_requests,
    })

# Allow students to request the teacher role
@login_required
@block_user_admin
def request_teacher_role(request):
    profile = request.user.profile
    if request.method == "POST" and profile.role == "student":
        if not profile.has_pending_teacher_request():
            explanation = request.POST.get("explanation", "").strip()
            requested_role = request.POST.get("requested_role", "teacher")
            if requested_role not in ("teacher", "producer"):
                requested_role = "teacher"
            RoleChangeRequest.objects.create(profile=profile, explanation=explanation, requested_role=requested_role)
    return redirect("profile")

# Admin decision on role requests
@login_required
@admin_only
def handle_role_request(request, request_id):
    if request.method == "POST":
        try:
            role_request = RoleChangeRequest.objects.select_related("profile__user").get(id=request_id, status="pending")
            action = request.POST.get("action")
            if action == "approve":
                role_request.profile.role = role_request.requested_role
                role_request.profile.save()
                role_request.status = "approved"
            elif action == "deny":
                role_request.status = "denied"
            role_request.reviewer = request.user
            role_request.reviewed_at = timezone.now()
            role_request.save()
        except RoleChangeRequest.DoesNotExist:
            pass
    return redirect("manage_roles")

# Allow User Administrator to update user roles
@login_required
@admin_only
def update_role(request, user_id):
    if request.method == "POST":
        try:
            profile = Profile.objects.get(user__id=user_id)
            new_role = request.POST.get("role")
            if new_role in ["student", "teacher", "producer"]:
                profile.role = new_role
                profile.save()
        except Profile.DoesNotExist:
            pass
    return redirect("manage_roles")

