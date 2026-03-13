from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse


def index(request):
    return HttpResponse("This works! Team Number: A-12; Members: Lillie Paris, Jamar Oldacre, Elsa Norman, Sid Luthra, Ayaan Siddiqui")


def profile(request):
    return render(request, 'users/profile.html')
