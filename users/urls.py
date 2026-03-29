from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit-role/", views.edit_role, name="edit_role"),
    path('upload/', views.upload_profile_files, name='upload_profile_files'),
]