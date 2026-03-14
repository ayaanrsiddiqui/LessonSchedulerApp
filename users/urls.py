from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("classes/add/", views.add_class, name="add_class"),
    path("classes/<int:class_id>/edit/", views.edit_class, name="edit_class"),
    path("classes/<int:class_id>/delete/", views.delete_class, name="delete_class")
]