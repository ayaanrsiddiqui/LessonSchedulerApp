from django.db import models
from django.contrib.auth.models import User

# Profile model, this will be usable for both dj teacher and student
class Profile(models.Model):
    # link user to User defined via google login
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.URLField(blank=True)
    is_djteacher = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class DJClass(models.Model):
    # related name will allow us to access all the dj class easily later
    dj = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dj_classes")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    requirements = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dj.username}: {self.start_time} - {self.end_time}"


