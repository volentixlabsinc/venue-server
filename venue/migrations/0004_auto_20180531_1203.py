# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-31 12:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0003_auto_20180528_1300'),
    ]

    operations = [
        migrations.RenameField(
            model_name='forumpost',
            old_name='influence_points_bonus',
            new_name='influence_bonus_pts',
        ),
    ]