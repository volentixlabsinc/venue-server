# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-16 11:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0011_forumprofile_forum_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='forumprofile',
            name='forum',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='forum_profiles', to='venue.ForumSite'),
        ),
    ]