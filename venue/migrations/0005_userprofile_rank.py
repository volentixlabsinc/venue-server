# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-09 13:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0004_auto_20180509_0829'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='rank',
            field=models.IntegerField(default=0),
        ),
    ]
