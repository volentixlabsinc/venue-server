# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-03 04:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0012_auto_20171216_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='uptimebatch',
            name='reason_closed',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]