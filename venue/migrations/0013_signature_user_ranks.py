# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-13 08:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0012_forumuserrank_forum_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='signature',
            name='user_ranks',
            field=models.ManyToManyField(related_name='signatures', to='venue.ForumUserRank'),
        ),
    ]