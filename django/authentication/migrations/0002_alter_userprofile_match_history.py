# Generated by Django 4.2.15 on 2024-08-30 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='match_history',
            field=models.JSONField(default=list),
        ),
    ]