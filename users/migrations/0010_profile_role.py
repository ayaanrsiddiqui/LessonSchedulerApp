# Add role field to Profile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_rolechangerequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin_user', 'User Administrator')], default='student', max_length=20),
        ),
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, max_length=1000),
        ),
    ]
