from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileUploadForm
from .models import Profile

@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, "users/profile.html", {"profile": profile})

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
        form = ProfileUploadForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileUploadForm(instance=profile)

    return render(request, "users/upload_files.html", {"form": form})
