import os
import uuid

import celery
from constance import config
from dateutil import parser
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Coalesce
from django.dispatch import receiver
from django.utils import timezone
from hashids import Hashids


def compute_total_points():
    total_points = settings.REDIS_DB.get('global_total_points')
    if not total_points:
        total_points = 0
    return round(float(total_points), 2)


class ForumSite(models.Model):
    """ Forum site names and addresses """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    scraper_name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ForumUserRank(models.Model):
    """ Names of forum user ranks/positions """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    forum_site = models.ForeignKey(ForumSite, related_name='ranks')
    name = models.CharField(max_length=30)
    bonus_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    allowed = models.BooleanField(default=False)

    def __str__(self):
        return self.name


def image_file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "sig_%s.%s" % (str(uuid.uuid4()), ext)
    return os.path.join('uploads', filename)


DEFAULT_SIGNATURE_IMAGE = os.path.join(
    'media',
    'uploads',
    'img',
    'signature_img.png'
)


class Signature(models.Model):
    """ Signature types per forum site """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)
    forum_site = models.ForeignKey(ForumSite, related_name='signature_types')
    user_ranks = models.ManyToManyField(
        ForumUserRank, related_name='signatures')
    code = models.TextField()
    test_signature = models.TextField(blank=True)
    image = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Language(models.Model):
    """ Site-wide language selection options """
    # TODO: Maybe we can use an Enum for a code field?
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """ Custom internal user profiles """
    # TODO: maybe change unique=True to OneToOneField to avoid
    # extra manipulations and call just by key
    # `user.profiles.language` ?
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='profiles', unique=True)
    language = models.ForeignKey(
        Language, null=True, blank=True, related_name='profiles')
    otp_secret = models.TextField(blank=True)
    enabled_2fa = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)
    receive_emails = models.BooleanField(default=False)
    referral_code = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.user.username

    @classmethod
    def get_by_referral_code(cls, referral_code):
        """
        Method returns user profile by referral_code or None
        :param referral_code: uuid generated with user creation
        :return: None or UserProfile object
        """
        if referral_code is None:
            return
        try:
            return cls.objects.get(referral_code=referral_code)
        except (cls.DoesNotExist, ValidationError):
            return

    @property
    def with_forum_profile(self):
        if self.forum_profiles.filter(active=True, verified=True).count() > 0:
            return True
        else:
            return False

    def get_num_posts(self, date=None):
        if date:
            date = parser.parse(date).date()
        else:
            date = timezone.now().date()
        num_posts = {
            'credited': 0,
            'pending': 0,
            'total': 0
        }
        for fp in self.forum_profiles.filter(verified=True):
            posts = fp.posts.filter(timestamp__date__lte=date)
            for post in posts:
                if post.date_credited and post.credited:
                    date_credited = post.date_credited.date()
                    if date_credited >= date:
                        num_posts['credited'] += 1
                if post.date_matured:
                    date_matured = post.date_matured.date()
                    if date_matured >= date:
                        num_posts['pending'] += 1
                else:
                    num_posts['pending'] += 1
                if post.timestamp.date() <= date:
                    num_posts['total'] += 1
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
        try:
            rank = rankings.latest().rank
        except Ranking.DoesNotExist:
            # Trigger ranking task if ranking does not exist
            job = celery.current_app.send_task(
                'venue.tasks.compute_ranking',
                queue='compute'
            )
            job.get()
            rankings = query_db(date)
            try:
                if rankings.latest():
                    rank = rankings.latest().rank
            except Ranking.DoesNotExist:
                rank = 0
        return rank

    @property
    def total_posts(self):
        posts = 0
        for fp in self.forum_profiles.filter(active=True, verified=True):
            posts += fp.total_posts
        return posts

    @property
    def total_points(self):
        points = 0
        for fp in self.forum_profiles.filter(active=True, verified=True):
            points += fp.total_points
        return round(float(points), 2)

    @property
    def referrals_bonuses(self):
        """
        Points from the referrals links
        :return: number of point from the referrals
        """
        bonuses_for_referrals = self.referrals.filter(
            granted=True,
            referral__forum_profiles__verified=True,
            referral__forum_profiles__active=True,
            referral__forum_profiles__dummy=False
        ).order_by('granted_at')[:config.MAX_REFERRALS].aggregate(
            bonuses=Coalesce(models.Sum('bonus'), 0.0)
        )
        return float(bonuses_for_referrals['bonuses'])

    @property
    def total_tokens(self):
        tokens = 0
        global_total_pts = compute_total_points()
        if global_total_pts:
            pct_contrib = self.total_points / global_total_pts
            tokens = pct_contrib * config.VTX_AVAILABLE
        tokens += self.referrals_bonuses
        return int(round(tokens, 0))


class Ranking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.IntegerField(default=1)
    user_profile = models.ForeignKey(
        UserProfile,
        related_name='rankings',
        on_delete=models.CASCADE
    )
    rank = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        get_latest_by = 'timestamp'


class ForumProfile(models.Model):
    """ Record of forum profile details per user """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        related_name='forum_profiles',
        on_delete=models.PROTECT
    )
    forum = models.ForeignKey(ForumSite, null=True,
                              blank=True, related_name='forum_profiles')
    forum_rank = models.ForeignKey(
        ForumUserRank, null=True, blank=True, related_name='users')
    forum_username = models.CharField(max_length=50, blank=True)
    forum_user_id = models.CharField(max_length=50, blank=True)
    profile_url = models.CharField(max_length=200, blank=True)
    signature = models.ForeignKey(
        Signature, null=True, blank=True, related_name='users')
    verification_code = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    date_verified = models.DateTimeField(null=True, blank=True)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(default=timezone.now)
    # Dummy account flag
    dummy = models.BooleanField(default=False)
    # The flag below is overwritten every scrape
    last_scrape = models.DateTimeField(null=True, blank=True)
    last_page_status = JSONField(default=list)

    class Meta:
        get_latest_by = 'date_updated'

    def __str__(self):
        return '%s @ %s' % (self.forum_user_id, self.forum.name)

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        try:
            before_save = type(self).objects.get(pk=self.pk) if self.pk else None
        except self.DoesNotExist:
            before_save = None
        super(ForumProfile, self).save(*args, **kwargs)
        if not self.verification_code:
            hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)
            forum_profile_id, forum_user_id = self.id, self.forum_user_id
            verification_code = hashids.encode(
                forum_profile_id, int(forum_user_id))
            ForumProfile.objects.filter(id=self.id).update(
                verification_code=verification_code)
        # add bonus to referrer
        object_is_created_or_changed = before_save is None or before_save.verified != self.verified
        # need to add bonus only once and when profile is verified
        # be careful, we don't verify dummy and active profile here,
        # because we want to keep all the history,
        # this part will be checked during request execution
        if self.verified and object_is_created_or_changed:
            referral_obj = Referral.objects.filter(referral=self.user_profile)
            # check if referrer exist
            if not len(referral_obj):
                return
            referral_obj = referral_obj[0]
            # check if user already get a bonus
            if referral_obj.granted:
                return
            # add a current amount of bonuses from the settings
            referral_obj.bonus = config.BONUSES_PER_REFERRALS
            referral_obj.granted = True
            referral_obj.granted_at = timezone.now()
            referral_obj.save()

    def get_last_scrape(self):
        if self.last_scrape:
            return self.last_scrape
        else:
            return self.date_verified

    @property
    def total_posts(self):
        count = 0
        if self.posts.exists():
            count = self.posts.filter(credited=True).count()
        return count

    @property
    def total_points(self):
        points = sum([x.total_points for x in self.posts.filter(credited=True)])
        return round(points, 2)


class ForumPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        related_name='posts',
        on_delete=models.PROTECT
    )
    forum_profile = models.ForeignKey(
        ForumProfile,
        related_name='posts',
        on_delete=models.PROTECT
    )
    topic_id = models.CharField(max_length=20)
    message_id = models.CharField(max_length=20, db_index=True)
    unique_content_length = models.IntegerField()
    timestamp = models.DateTimeField(db_index=True)
    monitoring = models.BooleanField(default=True)
    credited = models.BooleanField(default=True)
    matured = models.BooleanField(default=False)
    date_matured = models.DateTimeField(null=True, blank=True)
    date_credited = models.DateTimeField(default=timezone.now)
    base_points = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    forum_rank = models.ForeignKey(
        ForumUserRank,
        related_name='posts',
        on_delete=models.PROTECT
    )
    influence_bonus_pct = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0
    )
    influence_bonus_pts = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_points = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    valid_sig_minutes = models.IntegerField(default=0)
    invalid_sig_minutes = models.IntegerField(default=0)

    class Meta:
        get_latest_by = 'timestamp'

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        # Credit the points immediately
        if self._state.adding:
            base_points = config.POST_POINTS_MULTIPLIER
            bonus_pct = self.forum_profile.forum_rank.bonus_percentage
            influence_bonus = base_points * (float(bonus_pct) / 100)
            total_points = base_points + influence_bonus
            self.base_points = base_points
            self.influence_bonus_pct = bonus_pct
            self.influence_bonus_pts = influence_bonus
            self.total_points = total_points
        # Track the valid and invalid minutes, if post is not matured yet
        if not self.matured:
            try:
                current = ForumPost.objects.filter(
                    message_id=self.message_id).latest()
                last_scrape = self.forum_profile.get_last_scrape()
                last_scrape = last_scrape.replace(tzinfo=None)
                post_timestamp = self.timestamp.replace(tzinfo=None)
                if not self.forum_profile.last_scrape:
                    last_scrape = post_timestamp
                dt_now = timezone.now().replace(tzinfo=None)
                tdiff = dt_now - last_scrape
                tdiff_minutes = tdiff.total_seconds() / 60
                # Get status list, previous and current
                page_status_list = self.forum_profile.last_page_status
                if len(page_status_list) == 1:
                    previous_status = None
                    current_status = page_status_list[-1]
                elif len(page_status_list) == 2:
                    previous_status, current_status = page_status_list
                # Get details of the current status
                status_code = current_status.get('status_code')
                page_ok = current_status.get('page_ok')
                signature_found = current_status.get('signature_found')
                invalidate = False
                if status_code == 200:
                    if page_ok:
                        if not signature_found:
                            invalidate = True
                if invalidate:
                    self.invalid_sig_minutes = current.invalid_sig_minutes
                    self.invalid_sig_minutes += tdiff_minutes
                else:
                    self.valid_sig_minutes = current.valid_sig_minutes
                    self.valid_sig_minutes += tdiff_minutes
            except ForumPost.DoesNotExist:
                pass
        super(ForumPost, self).save(*args, **kwargs)


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


class Referral(models.Model):
    referral = models.ForeignKey(UserProfile, unique=True, related_name='referrer',
                                 help_text='User, that was registered with a referral code')
    referrer = models.ForeignKey(UserProfile, help_text='Owner of a referral code',
                                 related_name='referrals')
    bonus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(default=None, null=True, blank=True)


# --------------------
# Model change signals
# --------------------


@receiver(models.signals.post_delete, sender=UserProfile)
@receiver(models.signals.post_delete, sender=ForumProfile)
@receiver(models.signals.post_delete, sender=ForumPost)
def trigger_compute_ranking(*args, **kwargs):
    job = celery.current_app.send_task(
        'venue.tasks.compute_ranking',
        queue='compute'
    )
    job.get()
