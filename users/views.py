from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# only logged in users can access this page
@login_required
def profile_view(request):
    # get profile object from currently loggen in user
    profile = request.user.profile #profile model
    # renders the profile object
    return render(request, "users/profile.html", {"profile":profile})
