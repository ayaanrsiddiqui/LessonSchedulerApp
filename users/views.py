from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DJClass
from .forms import DJClassForm


# only logged in users can access this page
@login_required
def profile_view(request):
    # get profile object from currently loggen in user
    profile = request.user.profile #profile model
    # renders the profile object
    return render(request, "users/profile.html", {"profile":profile})

@login_required
def add_class(request):
    # only dj teachers can add a class
    if not request.user.profile.is_djteacher:
        messages.error(request, "Only DJ Teachers can add a class")
        return redirect('profile', username=request.user.username)

    # if form is submitted
    if request.method == "POST":
        form = DJClassFrom(request.POST)
        if form.is_valid():
            dj_class = form.save(commit=False)                
            dj_class.dj = request.user
            dj_class.save()
            messages.success(request, "Class added successfully")
            return redirect('profile', username=request.user.username)

    # empty form
    else:
        form = DJClassForm()
        
    return render(request, "classes/add_class.html", {"form": form})

@login_required
def edit_class(request, class_id):
    # fetch class with given id belonging to the logged in user
    dj_class = get_object_or_404(DJClass, id-class_id, dj=request.user)

    # if form submitted
    if request.method == "POST":
        form = DJClassFrorm(request.POST, instance=dj_class)
        if form.is_valid():
            form.save()
            message.success(request, "Class edited successfully")
            return redirect('profile', username=request.user.username)

    # if GET request
    else:
        form = DJClassForm(instance=dj_class)
    
    return render(request, "classes/edit_class.html", {"form": form})

@login_required
def delete_class(request, class_id):
    # get existing class of logged in user and given id
    dj_class = get_object_or_404(DJClass, id=class_id, dj=request.user)

    #User confirms delete
    if request.method == "POST":
        dj_class.delete()
        messages.success(request, "Class deleted successfully")
        return redirect('profile')
    
    return render(request, "classes/confirm_delete.html")