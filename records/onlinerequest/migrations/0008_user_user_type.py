# Generated by Django 4.2.11 on 2024-04-23 04:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinerequest', '0007_registerrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='user_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'student'), (2, 'teacher'), (3, 'secretary'), (4, 'supervisor'), (5, 'admin')], default=1),
        ),
    ]