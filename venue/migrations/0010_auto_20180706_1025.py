# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-06 10:25
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venue', '0009_forumprofile_last_page_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumprofile',
            name='last_page_status',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=list),
        ),
    ]
