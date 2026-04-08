# Generated migration to add max_length constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_rolechangerequest_explanation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='rolechangerequest',
            name='explanation',
            field=models.TextField(blank=True, max_length=1000),
        ),
    ]
