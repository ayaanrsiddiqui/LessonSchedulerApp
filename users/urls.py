from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("profile/<str:username>/", views.public_profile_view, name="public_profile"),
    path('upload/', views.upload_profile_files, name='upload_profile_files'),
    path('request-teacher/', views.request_teacher_role, name='request_teacher_role'),
    path('manage-roles/', views.manage_roles, name='manage_roles'),
    path('handle-role-request/<int:request_id>/', views.handle_role_request, name='handle_role_request'),
    path('update-role/<int:user_id>/', views.update_role, name='update_role'),
]