# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-06-16 04:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0008_forumprofile_dummy'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='rank',
        ),
    ]
