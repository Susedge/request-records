# Generated by Django 4.2.11 on 2024-04-23 08:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onlinerequest', '0013_rename_course_profile_course_code_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='course_code',
            new_name='course',
        ),
    ]
