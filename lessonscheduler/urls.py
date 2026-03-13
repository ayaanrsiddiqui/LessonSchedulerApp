from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('profile/', views.profile, name="profile"),
    path('accounts/', include('allauth.urls')),
]
