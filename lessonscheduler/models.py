# Description: Asymmetrical DJ/student scheduling data models with lessons, signups, and requests
# Generated with Copilot on March 29, 2026
# Prompt: build asymmetrical DJ/student class posting, signup, and request flow

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import Profile

DIFFICULTY_CHOICES = [
    ("Beginner", "Beginner"),
    ("Intermediate", "Intermediate"),
    ("Proficient", "Proficient"),
    ("Advanced", "Advanced"),
]

# Refactored for asymmetrical DJ/Student workflow (March 29, 2026)
class Lesson(models.Model):
    """Posted class by a DJ with capacity and requirements. Students sign up for these."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="lesson_images/", blank=True, null=True)
    location = models.CharField(max_length=300, default="TBD")
    capacity = models.PositiveIntegerField(default=10)
    

    experience_requirements = models.CharField(
        max_length=30,
        choices=DIFFICULTY_CHOICES
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    dj = models.ForeignKey(
        User,
        related_name="posted_lessons",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        errors = {}

        dj_id = getattr(self, "dj_id", None)
        now = timezone.now()

        if self.start_time and self.start_time <= now:
            errors["start_time"] = "Start time must be in the future."

        if self.end_time and self.end_time <= now:
            errors["end_time"] = "End time must be in the future."

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = "End time must be after start time."

        if dj_id and not Profile.objects.filter(
            user_id=dj_id, role='teacher'
        ).exists():
            errors["dj"] = "Only DJ accounts can post classes."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def current_enrollment_count(self):
        """Get current number of students signed up."""
        return ClassSignup.objects.filter(
            lesson=self,
            status="confirmed",
        ).count()

    @property
    def spots_available(self):
        """Get remaining available spots."""
        return max(0, self.capacity - self.current_enrollment_count)


class ClassSignup(models.Model):
    """Student enrollment in a DJ's posted class."""
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("waitlisted", "Waitlisted"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(
        User, related_name="class_signups", on_delete=models.CASCADE
    )
    lesson = models.ForeignKey(
        Lesson, related_name="signups", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    signed_up_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("student", "lesson")

    def clean(self):
        errors = {}

        # Only confirmed enrollments consume class capacity.
        if self.status == "confirmed" and self.lesson:
            confirmed_count = ClassSignup.objects.filter(
                lesson=self.lesson,
                status="confirmed",
            ).exclude(pk=self.pk).count()

            if confirmed_count >= self.lesson.capacity:
                errors["status"] = "This class is already full."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} -> {self.lesson.title}"


class ClassRequest(models.Model):
    """Student request for a specific date/time from a DJ."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("denied", "Denied"),
    ]

    student = models.ForeignKey(
        User, related_name="class_requests", on_delete=models.CASCADE
    )
    dj = models.ForeignKey(
        User, related_name="received_requests", on_delete=models.CASCADE
    )
    requested_start_time = models.DateTimeField()
    requested_end_time = models.DateTimeField()
    requested_skill_level = models.CharField(
        max_length=30,
        choices=DIFFICULTY_CHOICES,
        blank=True,
        default="Beginner",
    )
    requested_location = models.CharField(max_length=300, blank=True, default="")
    requested_equipment = models.TextField(blank=True, default="")

    description = models.TextField(help_text="Why you need this specific time/date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        errors = {}

        student_id = getattr(self, "student_id", None)
        dj_id = getattr(self, "dj_id", None)
        now = timezone.now()

        if student_id and dj_id and student_id == dj_id:
            errors["student"] = "Cannot request a class from yourself."

        if self.requested_start_time and self.requested_start_time <= now:
            errors["requested_start_time"] = "Requested start time must be in the future."

        if self.requested_end_time and self.requested_end_time <= now:
            errors["requested_end_time"] = "Requested end time must be in the future."

        if (
            self.requested_start_time
            and self.requested_end_time
            and self.requested_start_time >= self.requested_end_time
        ):
            errors["requested_end_time"] = "Requested end time must be after start time."

        if dj_id and not Profile.objects.filter(
            user_id=dj_id, role='teacher'
        ).exists():
            errors["dj"] = "Selected user is not a DJ."

        if errors:
            raise ValidationError(errors)

        

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} requests {self.dj.username} at {self.requested_start_time}"