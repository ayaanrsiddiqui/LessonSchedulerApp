# This migration is kept as a no-op because the Profile.role field
# is already introduced by the squashed migration 0008_squashed_users_rolechangerequest_complete.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_rolechangerequest'),
    ]

    operations = []
