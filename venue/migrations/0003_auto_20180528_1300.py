# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-28 13:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0002_auto_20180527_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumprofile',
            name='last_scrape',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]