# Generated by Django 5.0.7 on 2024-08-20 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_file_deleted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='directory',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]