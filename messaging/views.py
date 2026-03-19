from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from django.contrib.auth.models import User

@login_required
def inbox(request):
    messages = Message.objects.filter(recipient=request.user)
    return render(request, 'messaging/inbox.html', {'messages': messages})

@login_required
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, recipient=recipient, content=content)
            return redirect('inbox')
    return render(request, 'messaging/send_message.html', {'recipient': recipient})

@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'messaging/user_list.html', {'users': users})
