# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-27 22:13
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import venue.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic_id', models.CharField(max_length=20)),
                ('message_id', models.CharField(db_index=True, max_length=20)),
                ('unique_content_length', models.IntegerField()),
                ('timestamp', models.DateTimeField()),
                ('credited', models.BooleanField(default=False)),
                ('matured', models.BooleanField(default=False)),
                ('base_points', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('influence_bonus_pct', models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ('influence_points_bonus', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_points', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('valid_sig_minutes', models.IntegerField(default=0)),
                ('invalid_sig_minutes', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ForumProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forum_username', models.CharField(blank=True, max_length=50)),
                ('forum_user_id', models.CharField(blank=True, max_length=50)),
                ('profile_url', models.CharField(max_length=200)),
                ('verification_code', models.CharField(blank=True, max_length=20)),
                ('active', models.BooleanField(default=False)),
                ('verified', models.BooleanField(default=False)),
                ('date_verified', models.DateTimeField(blank=True, null=True)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('signature_found', models.BooleanField(default=False)),
                ('last_scrape', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='ForumSite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('address', models.CharField(max_length=50)),
                ('scraper_name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='ForumUserRank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('allowed', models.BooleanField(default=False)),
                ('forum_site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ranks', to='venue.ForumSite')),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('code', models.CharField(max_length=5)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=20)),
                ('text', models.CharField(max_length=100)),
                ('action_text', models.CharField(blank=True, max_length=30)),
                ('action_link', models.CharField(blank=True, max_length=100)),
                ('variant', models.CharField(choices=[('primary', 'Primary'), ('secondary', 'Secondary'), ('success', 'Success'), ('danger', 'Danger'), ('warning', 'Warning'), ('info', 'Info')], max_length=10)),
                ('dismissible', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('dismissed_by', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Ranking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Signature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('code', models.TextField()),
                ('expected_links', models.TextField(blank=True)),
                ('test_signature', models.TextField(blank=True)),
                ('image', models.ImageField(default='static/img/signature_img.png', upload_to=venue.models.image_file_name)),
                ('active', models.BooleanField(default=True)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('forum_site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signature_types', to='venue.ForumSite')),
                ('user_ranks', models.ManyToManyField(related_name='signatures', to='venue.ForumUserRank')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_secret', models.TextField(blank=True)),
                ('enabled_2fa', models.BooleanField(default=False)),
                ('email_confirmed', models.BooleanField(default=False)),
                ('receive_emails', models.BooleanField(default=False)),
                ('rank', models.IntegerField(default=0)),
                ('language', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to='venue.Language')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='ranking',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rankings', to='venue.UserProfile'),
        ),
        migrations.AddField(
            model_name='forumprofile',
            name='forum',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='forum_profiles', to='venue.ForumSite'),
        ),
        migrations.AddField(
            model_name='forumprofile',
            name='forum_rank',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='venue.ForumUserRank'),
        ),
        migrations.AddField(
            model_name='forumprofile',
            name='signature',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='venue.Signature'),
        ),
        migrations.AddField(
            model_name='forumprofile',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_profiles', to='venue.UserProfile'),
        ),
        migrations.AddField(
            model_name='forumpost',
            name='forum_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='posts', to='venue.ForumProfile'),
        ),
        migrations.AddField(
            model_name='forumpost',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='posts', to='venue.UserProfile'),
        ),
        migrations.AlterUniqueTogether(
            name='forumprofile',
            unique_together=set([('forum', 'forum_user_id', 'verified')]),
        ),
    ]
