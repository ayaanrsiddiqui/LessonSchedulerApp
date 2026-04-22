# Generated migration - Add role field and RoleChangeRequest model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_intro_audio_alter_profile_profile_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin_user', 'User Administrator')], default='student', max_length=20),
        ),
        migrations.CreateModel(
            name='RoleChangeRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_role', models.CharField(choices=[('teacher', 'Teacher')], default='teacher', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='pending', max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_requests', to='users.Profile')),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.SET_NULL, related_name='reviewed_role_requests', to='auth.User')),
            ],
        ),
    ]
