# Generated migration - Add explanation field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_profile_role_rolechangerequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolechangerequest',
            name='explanation',
            field=models.TextField(blank=True),
        ),
    ]
