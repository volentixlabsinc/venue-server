# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-07 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0014_auto_20180103_0429'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='otp_secret',
            field=models.TextField(blank=True),
        ),
    ]