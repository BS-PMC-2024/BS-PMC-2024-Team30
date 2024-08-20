# Generated by Django 5.0.7 on 2024-08-20 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_blocked_alter_user_user_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='directory',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='file',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='project',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
