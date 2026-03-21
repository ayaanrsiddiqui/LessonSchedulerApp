from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from django.contrib.auth.models import User
from django.db.models import Q

@login_required
def inbox(request):
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient').order_by('-timestamp')

    latest_per_peer = {}
    for msg in messages:
        peer = msg.recipient if msg.sender == request.user else msg.sender
        if peer.id not in latest_per_peer:
            latest_per_peer[peer.id] = {
                'peer': peer,
                'message': msg,
            }

    conversations = list(latest_per_peer.values())

    return render(request, 'messaging/inbox.html', {'conversations': conversations})

@login_required
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)
    users = User.objects.exclude(id=request.user.id)
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user))
    ).order_by('timestamp')
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, recipient=recipient, content=content)
            return redirect('send_message', username=username)
    return render(request, 'messaging/send_message.html', {
        'recipient': recipient,
        'messages': messages,
        'users': users,
    })

@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'messaging/user_list.html', {'users': users})
