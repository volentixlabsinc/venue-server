# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-09 08:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0003_auto_20180509_0821'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postuptimestats',
            name='invalid_sig_seconds',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='postuptimestats',
            name='valid_sig_seconds',
            field=models.IntegerField(),
        ),
    ]
