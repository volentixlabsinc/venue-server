# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-03 16:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0006_auto_20171103_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumprofile',
            name='profile_url',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='forumprofile',
            unique_together=set([('user_profile', 'forum_user_id')]),
        ),
    ]