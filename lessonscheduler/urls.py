# Description: URL routes for DJ/student dashboards, classes, signups, and class requests
# Generated with Copilot on March 29, 2026
# Prompt: add routes for asymmetrical DJ/student scheduling workflow

from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('profile/', views.profile, name="profile_redirect"),
    
    # DJ URLs
    path('dj/dashboard/', views.dj_dashboard, name='dj_dashboard'),
    path('lesson/create/', views.lesson_create, name='lesson_create'),
    path('lesson/<int:lesson_id>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lesson/<int:lesson_id>/detail/', views.dj_class_detail, name='dj_class_detail'),
    path('request/<int:request_id>/manage/', views.manage_request, name='manage_request'),
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('classes/browse/', views.browse_classes, name='browse_classes'),
    path('class/<int:lesson_id>/signup/', views.class_signup, name='class_signup'),
    path('dj/<int:dj_id>/request/', views.request_class, name='request_class'),
    
    # Auth URLs
    path('accounts/', include('allauth.urls')),
]
