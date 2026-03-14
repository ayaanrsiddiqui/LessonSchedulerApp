from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, "users/profile.html", {"profile": profile})

@login_required
def edit_role(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.is_djteacher = request.POST.get('is_djteacher') == 'true'
        profile.save()
        return redirect('profile')
    return render(request, "users/edit_role.html", {"profile": profile})
