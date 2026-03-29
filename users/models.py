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

    is_djteacher = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


