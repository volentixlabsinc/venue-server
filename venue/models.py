import os
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.db import models
from hashids import Hashids
from constance import config
import celery


def compute_total_points():
    total_points = settings.REDIS_DB.get('global_total_points')
    if not total_points:
        total_points = 0
    return round(float(total_points), 2)


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
    rank = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

    @property
    def with_forum_profile(self):
        if self.forum_profiles.count() > 0:
            return True
        else:
            return False

    def get_num_posts(self, date=None):
        num_posts = 0
        for fp in self.forum_profiles.filter(active=True):
            if not date:
                date = timezone.now().date()
            post_stats = fp.post_stats.filter(timestamp__date=str(date))
            if post_stats.last():
                num_posts += post_stats.last().num_posts
                num_posts -= fp.initial_posts_count
        return num_posts

    def get_ranking(self, date=None):
        if not date:
            date = timezone.now().date()

        def query_db(date):
            rankings = Ranking.objects.filter(
                user_profile_id=self.id,
                timestamp__date=str(date)
            )
            return rankings

        rankings = query_db(date)
        rank = None
        if rankings.last():
            rank = rankings.last().rank
        else:
            # Trigger ranking task if ranking does not exist
            job = celery.current_app.send_task(
                'venue.tasks.compute_ranking',
                queue='ranking'
            )
            job.get()
            rankings = query_db(date)
            if rankings.last():
                rank = rankings.last().rank
        return rank

    @property
    def total_posts(self):
        posts = 0
        for fp in self.forum_profiles.filter(active=True):
            if fp.post_stats.last():
                posts += fp.total_posts
        return posts

    @property
    def post_points(self):
        points = 0
        for fp in self.forum_profiles.filter(active=True):
            if fp.post_stats.last():
                points += fp.total_posts * config.POST_POINTS_MULTIPLIER
        return round(points, 2)

    @property
    def uptime_points(self):
        points = 0
        for fp in self.forum_profiles.filter(active=True):
            if fp.post_stats.last():
                uptime_stats = fp.post_stats.last().uptime_stats
                points = uptime_stats.valid_sig_seconds / 3600
                points *= config.UPTIME_POINTS_MULTIPLIER
        return round(points, 2)

    @property
    def total_points(self):
        points = self.post_points + self.uptime_points
        return round(points, 2)

    @property
    def total_tokens(self):
        tokens = 0
        global_total_pts = compute_total_points()
        if global_total_pts:
            pct_contrib = self.total_points / global_total_pts
            tokens = pct_contrib * config.VTX_AVAILABLE
        return int(round(tokens, 0))


class Ranking(models.Model):
    user_profile = models.ForeignKey(
        UserProfile,
        related_name='rankings'
    )
    rank = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)


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

    @property
    def initial_posts_count(self):
        post_stats = self.post_stats.first()
        return post_stats.num_posts

    @property
    def total_posts(self):
        post_stats = self.post_stats.last()
        return post_stats.num_posts - self.initial_posts_count

    @property
    def post_points(self):
        points = self.total_posts * config.POST_POINTS_MULTIPLIER
        return round(points, 2)

    @property
    def uptime_seconds(self):
        post_stats = self.post_stats.last()
        uptime_stats = post_stats.uptime_stats
        return uptime_stats.valid_sig_seconds

    @property
    def uptime_points(self):
        points = (self.uptime_seconds / 3600)
        points *= config.UPTIME_POINTS_MULTIPLIER
        return round(points, 2)

    @property
    def total_points(self):
        points = self.post_points + self.uptime_points
        return round(points, 2)


class PostUptimeStats(models.Model):
    user_post_stats = models.OneToOneField(
        'UserPostStats',
        related_name='uptime_stats',
        on_delete=models.PROTECT
    )
    valid_sig_seconds = models.IntegerField()
    invalid_sig_seconds = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = 'Post uptime stats'


class UserPostStats(models.Model):
    user_profile = models.ForeignKey(
        UserProfile,
        related_name='post_stats'
    )
    forum_profile = models.ForeignKey(
        ForumProfile,
        related_name='post_stats'
    )
    num_posts = models.IntegerField()
    is_signature_valid = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = 'User post stats'

    def save(self, *args, **kwargs):
        # Take the previous first
        previous = self.forum_profile.post_stats.last()
        # Save the current post stats
        super(UserPostStats, self).save(*args, **kwargs)
        # Process the recording of uptime stats
        valid_sig_seconds = 0
        invalid_sig_seconds = 0
        if previous:
            tdiff = self.timestamp - previous.uptime_stats.timestamp
            tdiff_seconds = tdiff.total_seconds()
            if self.is_signature_valid:
                valid_sig_seconds = previous.uptime_stats.valid_sig_seconds
                valid_sig_seconds += tdiff_seconds
                # Copy over the invalid sig seconds
                invalid_sig_seconds = previous.uptime_stats.invalid_sig_seconds
            else:
                invalid_sig_seconds = previous.uptime_stats.invalid_sig_seconds
                invalid_sig_seconds += tdiff_seconds
                # Copy over the valid sig seconds
                valid_sig_seconds = previous.uptime_stats.valid_sig_seconds
        uptime_stats = PostUptimeStats(
            user_post_stats_id=self.id,
            valid_sig_seconds=valid_sig_seconds,
            invalid_sig_seconds=invalid_sig_seconds
        )
        uptime_stats.save()


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
