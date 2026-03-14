from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('profile/', views.profile, name="profile_redirect"),
    path('lesson/create/', views.lesson_create, name='lesson_create'),
    path('accounts/', include('allauth.urls')),
]
