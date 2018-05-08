import os
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.db import models
from hashids import Hashids


class ForumSite(models.Model):
    """ Forum site names and addresses """
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    scraper_name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ForumUserRank(models.Model):
    """ Names of forum user ranks/positions """
    forum_site = models.ForeignKey(ForumSite, related_name='ranks')
    name = models.CharField(max_length=30)
    allowed = models.BooleanField(default=False)

    def __str__(self):
        return self.name


def image_file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "signature_%s.%s" % (instance.id, ext)
    return os.path.join('uploads', filename)


DEFAULT_SIGNATURE_IMAGE = os.path.join(
    'static',
    'img',
    'signature_img.png'
)


class Signature(models.Model):
    """ Signature types per forum site """
    name = models.CharField(max_length=30)
    forum_site = models.ForeignKey(ForumSite, related_name='signature_types')
    user_ranks = models.ManyToManyField(
        ForumUserRank, related_name='signatures')
    code = models.TextField()
    expected_links = models.TextField(blank=True)
    test_signature = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=image_file_name,
        default=DEFAULT_SIGNATURE_IMAGE
    )
    active = models.BooleanField(default=True)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Language(models.Model):
    """ Site-wide language selection options """
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """ Custom internal user profiles """
    user = models.ForeignKey(User, related_name='profiles')
    language = models.ForeignKey(
        Language, null=True, blank=True, related_name='profiles')
    otp_secret = models.TextField(blank=True)
    enabled_2fa = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @property
    def with_forum_profile(self):
        if self.forum_profiles.count() > 0:
            return True
        else:
            return False

    def get_daily_total_posts(self, date):
        pass

    def get_daily_new_posts(self, date):
        pass

    def get_total_posts_with_sig(self, latest_only=True):
        pass


class ForumProfile(models.Model):
    """ Record of forum profile details per user """
    user_profile = models.ForeignKey(
        UserProfile, related_name='forum_profiles')
    forum = models.ForeignKey(ForumSite, null=True,
                              blank=True, related_name='forum_profiles')
    forum_rank = models.ForeignKey(
        ForumUserRank, null=True, blank=True, related_name='users')
    forum_username = models.CharField(max_length=50, blank=True)
    forum_user_id = models.CharField(max_length=50, blank=True)
    profile_url = models.CharField(max_length=200)
    signature = models.ForeignKey(
        Signature, null=True, blank=True, related_name='users')
    verification_code = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    initial_posts_count = models.IntegerField(default=0)
    date_verified = models.DateTimeField(null=True, blank=True)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('forum', 'forum_user_id', 'verified')

    def __str__(self):
        return '%s @ %s' % (self.forum_user_id, self.forum.name)

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        super(ForumProfile, self).save(*args, **kwargs)
        if not self.verification_code:
            hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)
            forum_profile_id, forum_user_id = self.id, self.forum_user_id
            verification_code = hashids.encode(
                forum_profile_id, int(forum_user_id))
            ForumProfile.objects.filter(id=self.id).update(
                verification_code=verification_code)


class UserPostStats(models.Model):
    user_profile = models.ForeignKey(
        UserProfile,
        related_name='stats'
    )
    num_posts = models.IntegerField()
    is_signature_valid = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)


class UserCumTime(models.Model):
    user_post_stats = models.ForeignKey(
        UserPostStats,
        related_name='periods'
    )
    valid_sig_minutes = models.FloatField()
    invalid_sig_minutes = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)


class Notification(models.Model):
    code = models.CharField(max_length=20, blank=True)
    text = models.CharField(max_length=100)
    action_text = models.CharField(max_length=30, blank=True)
    action_link = models.CharField(max_length=100, blank=True)
    VARIANT_CHOICES = (
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info')
    )
    variant = models.CharField(max_length=10, choices=VARIANT_CHOICES)
    dismissible = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        User,
        related_name='notifications',
        on_delete=models.PROTECT
    )
    dismissed_by = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.text
