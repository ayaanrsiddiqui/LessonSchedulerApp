from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileUploadForm, ProfileBioForm
from .models import Profile

@login_required
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
def edit_role(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.is_djteacher = request.POST.get('is_djteacher') == 'true'
        profile.save()
        return redirect('profile')
    return render(request, "users/edit_role.html", {"profile": profile})

# Profile Picture and Audio upload
@login_required
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
