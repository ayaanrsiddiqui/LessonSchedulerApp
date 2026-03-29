# Description: Django admin registrations for lessons, class signups, and class requests
# Generated with Copilot on March 29, 2026
# Prompt: register new scheduling models in admin for management and visibility

from django.contrib import admin
from .models import Lesson, ClassSignup, ClassRequest

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'dj', 'start_time', 'capacity', 'created_at')
    list_filter = ('created_at', 'start_time')
    search_fields = ('title', 'dj__username', 'location')
    readonly_fields = ('created_at',)

@admin.register(ClassSignup)
class ClassSignupAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'status', 'signed_up_at')
    list_filter = ('status', 'signed_up_at')
    search_fields = ('student__username', 'lesson__title')
    readonly_fields = ('signed_up_at',)

@admin.register(ClassRequest)
class ClassRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'dj', 'requested_start_time', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('student__username', 'dj__username')
    readonly_fields = ('created_at',)
