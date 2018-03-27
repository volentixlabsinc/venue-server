# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-15 11:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('venue', '0016_userprofile_enabled_2fa'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=100)),
                ('action_text', models.CharField(blank=True, max_length=30)),
                ('action_link', models.CharField(blank=True, max_length=100)),
                ('dismissible', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('dismissed_by', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]