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


