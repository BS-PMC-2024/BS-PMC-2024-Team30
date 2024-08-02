# Generated by Django 5.0.7 on 2024-08-01 17:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_codedirectory_codefile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subdirectories', to='users.directory')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='directories', to='users.project')),
            ],
        ),
        migrations.AlterField(
            model_name='codefile',
            name='directory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='users.directory'),
        ),
        migrations.DeleteModel(
            name='CodeDirectory',
        ),
    ]