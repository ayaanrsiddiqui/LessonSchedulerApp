from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from .models import MessageAttachment
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from django.contrib import messages as flash_messages
from django.core.exceptions import ValidationError
from users.models import Profile
from users.decorators import block_user_admin

@login_required
@block_user_admin
def inbox(request):
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient').prefetch_related('attachments').order_by('-timestamp')

    latest_per_peer = {}
    for msg in messages:
        peer = msg.recipient if msg.sender == request.user else msg.sender
        if peer.pk not in latest_per_peer:
            latest_per_peer[peer.pk] = {
                'peer': peer,
                'message': msg,
            }

    conversations = list(latest_per_peer.values())

    students = User.objects.exclude(pk=request.user.pk).filter(profile__role='student').select_related('profile')
    teachers = User.objects.exclude(pk=request.user.pk).filter(profile__role='teacher').select_related('profile')

    return render(request, 'messaging/inbox.html', {
        'conversations': conversations,
        'students': students,
        'teachers': teachers,
    })

@login_required
@block_user_admin
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)
    users = User.objects.exclude(pk=request.user.pk)
    thread_messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user))
    ).select_related('sender', 'recipient').prefetch_related('attachments').order_by('timestamp')

    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        images = request.FILES.getlist('images')

        if not content and not images:
            flash_messages.error(
                request,
                'Enter a message or attach at least one image.',
                extra_tags='chat',
            )
            return redirect('send_message', username=username)

        try:
            with transaction.atomic():
                message = Message.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    content=content,
                )
                for image in images:
                    MessageAttachment.objects.create(message=message, image=image)
        except ValidationError as exc:
            flash_messages.error(request, '; '.join(exc.messages), extra_tags='chat')
            return redirect('send_message', username=username)
        except Exception:
            flash_messages.error(request, 'Could not send message. Please try again.', extra_tags='chat')
            return redirect('send_message', username=username)

        return redirect('send_message', username=username)

    return render(request, 'messaging/send_message.html', {
        'recipient': recipient,
        'thread_messages': thread_messages,
        'users': users,
    })
