from django.db import models
from django.contrib.auth.models import User

# dynamic upload paths in s3 for pfp and audio file
def profile_pic_upload_path(instance, filename):
    return f'uploads/profile_pics/user_{instance.user.id}/{filename}'

def audio_upload_path(instance, filename):
    return f'uploads/audio/user_{instance.user.id}/{filename}'

# Profile model, this will be usable for both dj teacher and student
class Profile(models.Model):
    # link user to User defined via google login
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)

    # optional uploadable fields
    profile_picture = models.ImageField(upload_to=profile_pic_upload_path, blank=True, null=True)
    intro_audio = models.FileField(upload_to=audio_upload_path, blank=True, null=True)

    # role choice for user type
    ROLE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("admin_user", "User Administrator"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")

    def __str__(self):
        return self.user.username
    
    def is_user_admin(self):
        return self.role == "admin_user"

    def has_pending_teacher_request(self):
        return self.role_requests.filter(status="pending", requested_role="teacher").exists()


class RoleChangeRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="role_requests")
    requested_role = models.CharField(max_length=20, choices=[("teacher", "Teacher")], default="teacher")
    explanation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_role_requests")

    def __str__(self):
        return f"{self.profile.user.username} requests {self.requested_role} ({self.status})"


