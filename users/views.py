from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileUploadForm, ProfileBioForm
from .models import Profile
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

    return render(request, "users/profile.html", {"profile": profile, "bio_form": bio_form})

# Description: Profile display and role editing views
# Generated with Copilot on March 14, 2026
# Prompt: could a user add a page where the user can change their profile type whenever they would like?
@login_required
@block_user_admin
def edit_role(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.role = request.POST.get('role')
        profile.save()
        return redirect('profile')
    return render(request, "users/edit_role.html", {"profile": profile})

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

    return render(request, "users/manage_roles.html", {"users": users})

# Allow User Administrator to update user roles
@login_required
@admin_only
def update_role(request, user_id):
    if request.method == "POST":
        try:
            profile = Profile.objects.get(user__id=user_id)
            new_role = request.POST.get("role")
            if new_role in ["student", "teacher"]:
                profile.role = new_role
                profile.save()
        except Profile.DoesNotExist:
            pass
    return redirect("manage_roles")

