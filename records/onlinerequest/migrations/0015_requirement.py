# Generated by Django 4.2.11 on 2024-04-24 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinerequest', '0014_rename_course_code_profile_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='Requirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=64)),
                ('no_of_files', models.PositiveSmallIntegerField()),
            ],
        ),
    ]
