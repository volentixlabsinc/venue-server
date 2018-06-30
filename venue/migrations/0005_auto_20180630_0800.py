# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-06-30 08:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0004_auto_20180629_0732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumprofile',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='forum_profiles', to='venue.UserProfile'),
        ),
    ]
