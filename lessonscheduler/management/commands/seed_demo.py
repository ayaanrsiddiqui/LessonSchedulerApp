"""Populate the database with a small, coherent set of demo content.

Written so the deployed site is not an empty shell for anyone who signs in to
look at it. Everything it creates is prefixed ``demo_`` and carries an unusable
password, so none of these accounts can be logged into -- they exist to be read,
not used.

Idempotent: every object is created with get_or_create, so running it twice
changes nothing. ``--clear`` removes the demo accounts (and, by cascade, their
lessons, signups, requests and messages) without touching real users.

    python manage.py seed_demo
    python manage.py seed_demo --clear

The model layer validates on save (Lesson.save and ClassSignup.save both call
full_clean), so this command has to satisfy the same rules the forms do:
lessons must start and end in the future on one calendar day, only teacher or
producer profiles may post them, and confirmed signups may not exceed capacity.
Dates are therefore computed relative to now at run time rather than hardcoded.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from lessonscheduler.models import ClassRequest, ClassSignup, Lesson
from messaging.models import Message
from users.models import Profile, RoleChangeRequest

DEMO_PREFIX = "demo_"


# (username, first, last, role, bio)
PEOPLE = [
    (
        "demo_marcus",
        "Marcus",
        "Bell",
        "teacher",
        "Resident DJ at two Charlottesville venues. I teach beatmatching by ear "
        "first and let you touch the sync button afterwards. Six years behind "
        "CDJs, three of them teaching.",
    ),
    (
        "demo_priya",
        "Priya",
        "Raghavan",
        "teacher",
        "Open-format and Bollywood-fusion sets. I mostly work with people who "
        "have played a party or two and want their transitions to stop being "
        "obvious.",
    ),
    (
        "demo_devon",
        "Devon",
        "Clarke",
        "producer",
        "I make beats in Ableton and FL and teach both. Sampling, drum "
        "programming, and getting a track to sit right in a mix without a "
        "mastering engineer.",
    ),
    ("demo_alex", "Alex", "Nguyen", "student", "Second year. Never touched a controller before this semester."),
    ("demo_jordan", "Jordan", "Ellis", "student", "Play house sets at friends' apartments. Want to get tighter."),
    ("demo_sam", "Sam", "Okafor", "student", "Producer-curious. Mostly here for the Ableton sessions."),
    ("demo_riley", "Riley", "Tran", "student", "Third year, been mixing about a year."),
    ("demo_casey", "Casey", "Moore", "student", "Complete beginner, signed up on a whim."),
    ("demo_taylor", "Taylor", "Brooks", "student", "Radio show host looking to DJ live."),
]


def _slot(days_ahead, start_hour, hours):
    """A start/end pair that lands entirely inside one calendar day."""
    base = timezone.now() + timedelta(days=days_ahead)
    start = base.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    return start, start + timedelta(hours=hours)


# (key, title, dj username, level, capacity, location, days ahead, hour, length, description)
LESSONS = [
    (
        "beatmatch",
        "Beatmatching Without Sync",
        "demo_marcus",
        "Beginner",
        8,
        "Newcomb Hall, Room 389",
        4,
        18,
        2,
        "Pitch fader, jog wheel, and your ears. We spend the whole two hours on "
        "one skill: hearing which track is running fast and fixing it before the "
        "phrase ends. Bring headphones. Controllers provided.",
    ),
    (
        "transitions",
        "Transitions That Aren't Obvious",
        "demo_priya",
        "Intermediate",
        6,
        "Newcomb Hall, Room 389",
        6,
        19,
        2,
        "You can mix two tracks together. This is about where to do it. Phrase "
        "counting, EQ swaps, filter sweeps, and when to just cut. Come with two "
        "tracks you already like playing together.",
    ),
    (
        "ableton",
        "Ableton From an Empty Project",
        "demo_devon",
        "Beginner",
        10,
        "Clemons Library, Robertson Media Center",
        8,
        17,
        3,
        "Start with nothing and leave with a sixteen-bar loop. Drum rack, one "
        "sampled chop, and a bassline. Laptops encouraged; a few are available "
        "if you don't have one.",
    ),
    (
        "drums",
        "Drum Programming and Groove",
        "demo_devon",
        "Intermediate",
        3,
        "Clemons Library, Robertson Media Center",
        11,
        18,
        2,
        "Why your drums sound stiff. Swing, velocity, ghost notes, and choosing "
        "samples that leave room for each other. Bring a loop you're unhappy with.",
    ),
    (
        "harmonic",
        "Harmonic Mixing and Key Reading",
        "demo_priya",
        "Proficient",
        6,
        "Newcomb Hall, Room 389",
        14,
        19,
        2,
        "Camelot wheel, energy levels, and when key clash is actually fine. "
        "Assumes you're comfortable mixing and want to plan a set instead of "
        "improvising one.",
    ),
    (
        "closing",
        "Reading a Room and Closing a Set",
        "demo_marcus",
        "Advanced",
        5,
        "Off-grounds — venue TBD, details by message",
        18,
        20,
        2,
        "The part nobody teaches. Pacing an hour, recovering from a dead floor, "
        "and how to end. For people already playing out.",
    ),
]


class Command(BaseCommand):
    help = "Create demo teachers, students, lessons, signups, requests and messages."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete the demo accounts and everything attached to them, then stop.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = User.objects.filter(username__startswith=DEMO_PREFIX).delete()
            self.stdout.write(self.style.SUCCESS(f"Removed demo data ({deleted} rows)."))
            return

        users = self._create_people()
        lessons = self._create_lessons(users)
        self._create_signups(users, lessons)
        self._create_requests(users, lessons)
        self._create_messages(users, lessons)
        self._create_role_request(users)
        self._promote_superusers()

        self.stdout.write(self.style.SUCCESS("Demo data is in place."))

    # ------------------------------------------------------------------ people

    def _create_people(self):
        users = {}
        for username, first, last, role, bio in PEOPLE:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@example.com",
                },
            )
            if created:
                # Nobody can sign in as a demo account.
                user.set_unusable_password()
                user.save(update_fields=["password"])

            # users.signals creates the Profile on user creation with role
            # "student"; get_or_create covers the case where the signal is
            # disconnected or the user predates it.
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.role != role or profile.bio != bio:
                profile.role = role
                profile.bio = bio
                profile.save(update_fields=["role", "bio"])

            users[username] = user

        self.stdout.write(f"  people: {len(users)}")
        return users

    # ----------------------------------------------------------------- lessons

    def _create_lessons(self, users):
        lessons = {}
        for (
            key,
            title,
            dj_username,
            level,
            capacity,
            location,
            days_ahead,
            hour,
            length,
            description,
        ) in LESSONS:
            start, end = _slot(days_ahead, hour, length)
            lesson, _ = Lesson.objects.get_or_create(
                title=title,
                dj=users[dj_username],
                defaults={
                    "description": description,
                    "location": location,
                    "capacity": capacity,
                    "experience_requirements": level,
                    "start_time": start,
                    "end_time": end,
                },
            )
            lessons[key] = lesson

        self.stdout.write(f"  lessons: {len(lessons)}")
        return lessons

    # ----------------------------------------------------------------- signups

    def _create_signups(self, users, lessons):
        # "drums" has capacity 3, so the last two students land on the waitlist
        # and the lesson shows the waitlist behaviour on the site.
        plan = [
            ("beatmatch", ["demo_alex", "demo_casey", "demo_taylor", "demo_riley"]),
            ("transitions", ["demo_jordan", "demo_riley"]),
            ("ableton", ["demo_sam", "demo_alex", "demo_casey"]),
            ("drums", ["demo_sam", "demo_jordan", "demo_riley", "demo_taylor", "demo_alex"]),
            ("harmonic", ["demo_jordan"]),
        ]

        count = 0
        for lesson_key, usernames in plan:
            lesson = lessons[lesson_key]
            confirmed = ClassSignup.objects.filter(lesson=lesson, status="confirmed").count()
            for offset, username in enumerate(usernames):
                status = "confirmed" if confirmed < lesson.capacity else "waitlisted"
                _, created = ClassSignup.objects.get_or_create(
                    student=users[username],
                    lesson=lesson,
                    defaults={
                        "status": status,
                        # Stagger so waitlist ordering is deterministic.
                        "signed_up_at": timezone.now() - timedelta(hours=len(usernames) - offset),
                    },
                )
                if created:
                    count += 1
                    if status == "confirmed":
                        confirmed += 1

        self.stdout.write(f"  signups: {count} new")

    # ---------------------------------------------------------------- requests

    def _create_requests(self, users, lessons):
        pending_start, pending_end = _slot(9, 16, 2)
        other_start, other_end = _slot(12, 20, 1)
        past_start, past_end = _slot(7, 18, 2)

        specs = [
            {
                "student": users["demo_casey"],
                "dj": users["demo_marcus"],
                "request_type": "new",
                "requested_start_time": pending_start,
                "requested_end_time": pending_end,
                "requested_skill_level": "Beginner",
                "requested_location": "Newcomb Hall, Room 389",
                "requested_equipment": "Would need to borrow a controller and headphones.",
                "description": (
                    "I have class every evening this semester so I can never make "
                    "the 6pm sessions. Is an afternoon slot possible?"
                ),
                "status": "pending",
            },
            {
                "student": users["demo_sam"],
                "dj": users["demo_devon"],
                "request_type": "new",
                "requested_start_time": other_start,
                "requested_end_time": other_end,
                "requested_skill_level": "Intermediate",
                "requested_location": "Clemons Library, Robertson Media Center",
                "requested_equipment": "Laptop with Ableton, my own headphones.",
                "description": (
                    "Working on a track for the showcase and I'm stuck on the "
                    "arrangement. An hour one-on-one would help more than a group "
                    "session."
                ),
                "status": "pending",
            },
            {
                "student": users["demo_riley"],
                "dj": users["demo_priya"],
                "request_type": "edit",
                "lesson": lessons["transitions"],
                "requested_start_time": past_start,
                "requested_end_time": past_end,
                "requested_skill_level": "Intermediate",
                "requested_location": "Newcomb Hall, Room 389",
                "requested_equipment": "",
                "description": "Could this one start an hour later? Several of us have a 6pm lab.",
                "status": "accepted",
                "responded_at": timezone.now() - timedelta(days=1),
            },
        ]

        count = 0
        for spec in specs:
            lookup = {
                "student": spec["student"],
                "dj": spec["dj"],
                "requested_start_time": spec["requested_start_time"],
            }
            defaults = {k: v for k, v in spec.items() if k not in lookup}
            _, created = ClassRequest.objects.get_or_create(**lookup, defaults=defaults)
            if created:
                count += 1

        self.stdout.write(f"  class requests: {count} new")

    # ---------------------------------------------------------------- messages

    def _create_messages(self, users, lessons):
        threads = [
            ("demo_alex", "demo_marcus", "Is Thursday's beatmatching session still on? First time coming.", True),
            ("demo_marcus", "demo_alex", "It is. Come a few minutes early and I'll get you set up on a controller.", True),
            ("demo_alex", "demo_marcus", "Perfect, thanks.", True),
            ("demo_sam", "demo_devon", "Do I need Ableton installed beforehand or is the trial fine?", True),
            ("demo_devon", "demo_sam", "Trial is fine. Ninety days, full version, no save limit.", False),
            ("demo_jordan", "demo_priya", "Any prep for harmonic mixing? I've never used the Camelot wheel.", True),
            (
                "demo_priya",
                "demo_jordan",
                "Nothing required. Bring eight tracks you'd actually play and we'll key them together.",
                False,
            ),
            ("demo_taylor", "demo_marcus", "I'm on the waitlist for drum programming — does that usually move?", False),
        ]

        count = 0
        for sender, recipient, content, is_read in threads:
            _, created = Message.objects.get_or_create(
                sender=users[sender],
                recipient=users[recipient],
                content=content,
                defaults={"is_read": is_read},
            )
            if created:
                count += 1

        self.stdout.write(f"  messages: {count} new")

    # ------------------------------------------------------------ role request

    def _create_role_request(self, users):
        profile = users["demo_riley"].profile
        _, created = RoleChangeRequest.objects.get_or_create(
            profile=profile,
            requested_role="teacher",
            defaults={
                "explanation": (
                    "I've been mixing about a year and I've covered two of Marcus's "
                    "beginner sessions when he couldn't make it. Happy to start with "
                    "the intro slot."
                ),
                "status": "pending",
            },
        )
        self.stdout.write(f"  role change requests: {1 if created else 0} new")

    # -------------------------------------------------------------- superusers

    def _promote_superusers(self):
        """Give every superuser the in-app administrator role.

        Django's is_superuser flag governs /admin/; this project's user
        administration screens key off Profile.role instead, so a fresh
        superuser would otherwise see the site as a student.
        """
        promoted = []
        for user in User.objects.filter(is_superuser=True):
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.role != "admin_user":
                profile.role = "admin_user"
                profile.save(update_fields=["role"])
                promoted.append(user.username)

        if promoted:
            self.stdout.write(f"  promoted to admin_user: {', '.join(promoted)}")
        elif not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING(
                    "  no superuser exists yet -- run createsuperuser, then re-run "
                    "this command to give it the admin_user role."
                )
            )
