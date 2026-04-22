import os

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def _message_image_upload_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    return f"messages/user_{instance.message.sender_id}/{instance.message_id}_{instance.upload_token}{extension}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.recipient}"


class MessageAttachment(models.Model):
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    image = models.ImageField(upload_to=_message_image_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload_token = models.CharField(max_length=32, default="")

    class Meta:
        ordering = ["uploaded_at"]

    def clean(self):
        errors = {}

        if self.image:
            extension = os.path.splitext(self.image.name)[1].lower()
            if extension not in self.ALLOWED_EXTENSIONS:
                errors["image"] = "Unsupported image format. Use JPG, PNG, WEBP, or GIF."

            if self.image.size > self.MAX_FILE_SIZE_BYTES:
                errors["image"] = "Image must be 5MB or smaller."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.upload_token:
            self.upload_token = os.urandom(8).hex()
        self.full_clean()
        super().save(*args, **kwargs)