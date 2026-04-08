# Generated migration for explanation field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_profile_is_djteacher_profile_role_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolechangerequest',
            name='explanation',
            field=models.TextField(blank=True),
        ),
    ]
