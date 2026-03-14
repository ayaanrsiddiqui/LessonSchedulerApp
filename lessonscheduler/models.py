from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from users.models import Profile


## Copilot, 3/14/2026: Added Lesson model with validation to ensure teacher and student are not the same and that the teacher is marked as a teacher in their profile.
class Lesson(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    teacher = models.ForeignKey(
        User, related_name="lessons_as_teacher", on_delete=models.CASCADE
    )
    student = models.ForeignKey(
        User, related_name="lessons_as_student", on_delete=models.CASCADE
    )

    def clean(self):
        errors = {}

        teacher_id = getattr(self, "teacher_id", None)
        student_id = getattr(self, "student_id", None)

        if teacher_id and student_id and teacher_id == student_id:
            errors["student"] = "Teacher and student cannot be the same user."

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = "End time must be after start time."

        if teacher_id and not Profile.objects.filter(
            user_id=teacher_id, is_djteacher=True
        ).exists():
            errors["teacher"] = "Selected teacher account is not marked as a teacher."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title