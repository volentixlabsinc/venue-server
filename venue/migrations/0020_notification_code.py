# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-15 13:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0019_auto_20180315_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='code',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
