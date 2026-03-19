from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('send/<str:username>/', views.send_message, name='send_message'),
    path('send/', views.user_list, name='user_list'),
]