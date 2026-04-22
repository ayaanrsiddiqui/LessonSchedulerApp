# This migration is kept as a no-op because the RoleChangeRequest table
# is already created by the squashed migration 0008_squashed_users_rolechangerequest_complete.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_profile_id_alter_rolechangerequest_id'),
    ]

    operations = []
