import os
import decimal
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.db import models
from constance import config
from hashids import Hashids
import pandas as pd


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

    @property
    def with_forum_profile(self):
        if self.forum_profiles.count() > 0:
            return True
        else:
            return False

    def __str__(self):
        return self.user.username

    def get_daily_total_posts(self, date):
        value = 0
        checks = SignatureCheck.objects.filter(
            forum_profile__user_profile_id=self.id,
            date_checked__date=date)
        if checks.exists():
            data = [{'id': x.id, 'profile': x.forum_profile.id,
                     'posts': x.total_posts} for x in checks]
            df = pd.DataFrame(data)
            df = df.groupby('profile').agg({'posts': 'max'})
            value = int(df['posts'].sum())
        return value

    def get_daily_new_posts(self, date):
        value = 0
        checks = SignatureCheck.objects.filter(
            forum_profile__user_profile_id=self.id,
            date_checked__date=date, new_posts__gt=0).exclude(initial=True)
        if checks.exists():
            value = sum([x.get_new_posts() for x in checks])
        return value

    def get_total_posts(self):
        value = 0
        if self.get_total_posts_with_sig():
            total_per_forum = []
            for site in self.forum_profiles.filter(verified=True):
                if site.uptime_batches.count():
                    for batch in site.uptime_batches.all():
                        total_per_forum.append(batch.get_total_posts())
            value = sum(total_per_forum)
        return value

    def get_total_posts_with_sig(self, latest_only=True):
        total_per_forum = []
        for site in self.forum_profiles.filter(verified=True):
            if site.uptime_batches.count():
                posts_with_sig = site.get_total_posts_with_sig(
                    latest_only=latest_only)
                total_per_forum.append(posts_with_sig)
        return sum(total_per_forum)

    def get_total_days(self):
        value = 0
        if self.get_total_posts_with_sig(latest_only=True):
            total_per_forum = []
            for site in self.forum_profiles.filter(verified=True):
                if site.uptime_batches.count():
                    for batch in site.uptime_batches.all():
                        total_per_forum.append(batch.get_total_days())
            value = sum(total_per_forum)
        return value

    def get_post_points(self):
        value = 0
        for site in self.forum_profiles.filter(verified=True):
            if site.uptime_batches.count():
                latest_batch = site.uptime_batches.last()
                # for batch in site.uptime_batches.all():
                value += latest_batch.get_post_points()
        return value

    def get_post_days_points(self):
        value = 0
        for site in self.forum_profiles.filter(verified=True):
            if site.uptime_batches.count():
                for batch in site.uptime_batches.all():
                    value += batch.get_post_days_points()
        return value

    def get_influence_points(self):
        value = 0
        for site in self.forum_profiles.filter(verified=True):
            if site.uptime_batches.count():
                latest_batch = site.uptime_batches.last()
                # for batch in site.uptime_batches.all():
                value += latest_batch.get_influence_points()
        return value

    def get_total_points(self, date=None):
        value = 0
        if self.get_total_posts_with_sig():
            total_per_forum = []
            for site in self.forum_profiles.filter(verified=True):
                for batch in site.uptime_batches.all():
                    total_points = batch.get_total_points(date=date)
                    total_per_forum.append(total_points)
            value = sum(total_per_forum)
        return value

    def get_ranking(self, date=None):
        rank = None
        if date:
            ranking_check = self.rankings.filter(ranking_date__date=date)
            if ranking_check.exists():
                rank = ranking_check.last().rank
        else:
            latest_ranking = self.rankings.last()
            if latest_ranking:
                rank = latest_ranking.rank
        return rank

    def get_total_tokens(self):
        total_points = self.get_total_points()
        tokens = (total_points * config.VTX_AVAILABLE) / 10000
        return round(tokens, 2)


class Ranking(models.Model):
    """ Record of the daily rankings """
    user_profile = models.ForeignKey(UserProfile, related_name='rankings')
    ranking_date = models.DateTimeField(default=timezone.now)
    rank = models.IntegerField()

    def __str__(self):
        return '%s => #%s' % (self.user_profile.user.username, self.rank)


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

    def get_total_posts(self, actual=True):
        value = 0
        latest_batch = self.uptime_batches.last()
        if latest_batch:
            value = latest_batch.get_total_posts(actual=actual)
        return value

    def get_total_posts_with_sig(self, latest_only=True):
        value = 0
        if self.uptime_batches.count():
            latest_batch = self.uptime_batches.last()
            value = latest_batch.get_total_posts_with_sig(
                latest_only=latest_only)
        return value

    def get_total_days(self):
        value = 0
        if self.uptime_batches.count():
            value = sum([x.get_total_days()
                         for x in self.uptime_batches.all()])
        return value

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

    class Meta:
        unique_together = ('forum', 'forum_user_id', 'verified')


class GlobalStats(models.Model):
    """ Records the sitewide or global stats """
    total_posts = models.IntegerField()
    total_posts_with_sig = models.IntegerField()
    total_days = models.DecimalField(max_digits=12, decimal_places=4)
    date_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Global stats'


class UptimeBatch(models.Model):
    """ Grouping of calculation results into periods of continuous uptime """
    forum_profile = models.ForeignKey(
        ForumProfile, related_name='uptime_batches')
    date_started = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    date_ended = models.DateTimeField(null=True, blank=True)
    reason_closed = models.CharField(max_length=100, blank=True)
    num_deleted_posts = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Uptime batches'

    def __str__(self):
        return str(self.id)

    def get_batch_number(self):
        batch_ids = self.forum_profile.uptime_batches.all().values_list('id', flat=True)
        batch_ids = list(batch_ids)
        return sorted(batch_ids).index(self.id) + 1

    def get_total_posts(self, actual=False):
        value = 0
        latest_batch = self.forum_profile.uptime_batches.last()
        if latest_batch:
            if actual:
                latest_check = latest_batch.regular_checks.last()
                if latest_check:
                    value = latest_check.total_posts
            else:
                if self.forum_profile.get_total_posts_with_sig():
                    if latest_batch.id == self.id:
                        latest_check = latest_batch.regular_checks.last()
                        value = latest_check.total_posts
        return value

    def get_total_posts_with_sig(self, latest_only=True):
        value = 0
        latest_batch = self.forum_profile.uptime_batches.last()
        if latest_batch:
            if latest_only:
                if self.id == latest_batch.id:
                    if self.regular_checks.count() > 0:
                        value = sum(
                            [x.new_posts for x in self.regular_checks.all()])
            else:
                for check in self.regular_checks.all():
                    value += check.new_posts
        return value

    def get_total_days(self):
        value = 0
        if self.get_total_posts_with_sig(latest_only=False):
            if self.regular_checks.count() > 1:
                earliest_check = self.regular_checks.filter(
                    signature_found=True, new_posts__gt=0).first()
                if earliest_check:
                    latest_check = self.regular_checks.filter(
                        signature_found=True).last()
                    earliest_check_date = earliest_check.date_checked
                    latest_check_date = latest_check.date_checked
                    tdiff = latest_check_date - earliest_check_date
                    days = tdiff.total_seconds() / 86400  # converts total seconds to days
                    value = round(days, 4)
        return value

    def get_post_points(self):
        pts = 0
        try:
            latest_gs = GlobalStats.objects.last()
            pts = decimal.Decimal(self.get_total_posts_with_sig() * 6000)
            pts /= latest_gs.total_posts_with_sig
        except (decimal.InvalidOperation, decimal.DivisionByZero, AttributeError):
            pass
        return round(pts, 4)

    def get_post_days_points(self):
        pts = 0
        try:
            latest_gs = GlobalStats.objects.last()
            pts = decimal.Decimal(self.get_total_days() * 3800)
            pts /= latest_gs.total_days
        except (decimal.InvalidOperation, decimal.DivisionByZero, AttributeError):
            pass
        return round(pts, 4)

    def get_influence_points(self):
        pts = 0
        errors = (
            decimal.InvalidOperation,
            decimal.DivisionByZero,
            AttributeError
        )
        if self.get_total_posts():
            try:
                latest_gs = GlobalStats.objects.last()
                pts = decimal.Decimal(self.get_total_posts() * 200)
                pts /= latest_gs.total_posts
            except errors:
                pass
        return round(pts, 4)

    def get_total_points(self, date=None):
        post_points = self.get_post_points()
        uptime_points = self.get_post_days_points()
        influence_points = self.get_influence_points()
        total_points = post_points + uptime_points + influence_points
        return total_points


class SignaturePoints(models.Model):
    """ Tally of points for the signature campaign 
    
    How do we assign points for post uptime?
    When we compute for uptime points we only have to consider the posts in the latest 
    active batch since post count is carried over across batches.
    So, for every signature check, we will:
    1. Iterate over all the signature checks in the latest batch
    2. For any given signature check with new posts,  check when was the last time 
        that uptime points have been credited to it
    3. Get that time and compute the difference with the current time and compute 
        how many hours have elapsed since
    4. Get that number of hours and multiply with `config.POINTS_POST_UPTIME`
    """
    CATEGORY_CHOICES = (
        ('post_addition', 'Post addition'),
        ('post_deletion', 'Post deletion'),
        ('post_uptime', 'Uptime')
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='uptime'
    )
    forum_profile = models.ForeignKey(
        ForumProfile,
        related_name='points',
        on_delete=models.PROTECT
    )
    uptime_batch = models.ForeignKey(
        UptimeBatch,
        related_name='points',
        on_delete=models.PROTECT
    )
    signature_check = models.ForeignKey(
        'SignatureCheck',
        related_name='points',
        on_delete=models.PROTECT
    )
    posts_count = models.IntegerField()
    points = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['category'], name='category'),
            models.Index(fields=['timestamp'], name='timestamp'),
        ]
        verbose_name_plural = 'Signature points'

    def __str__(self):
        return str(self.id)


class SignatureCheck(models.Model):
    """ Results of regular scraping from forum profile pages 
    
    The scraping only gets the total posts in a forum profile and does not
    provide the number of new posts for each check. That number has to be
    determined by subtracting the total posts from the last signature check
    from the total posts of the current check.

    However, when a new batch is created by a signature check (either because
    of post deletion or removal of signature), the number of new posts has to be
    computed differently. In such a scenario, the number of new posts from the
    last check of the previous batch has to be carried over to the current check.
    In the case of post deletion, an additional step has to be done. The number
    of deleted posts has to be subtracted from the carried over number of new posts.
    
    Why carry over new posts count?
    It's a design decision for simplicity. We want the latest uptime batch
    to contain the actual running count of new posts. The idea is that when we add up
    the new posts of all the signature checks in a batch, it should give cumulative
    count of posts made since the user started using our signature minus the deleted
    posts.
    """
    forum_profile = models.ForeignKey(
        ForumProfile, related_name='regular_checks')
    uptime_batch = models.ForeignKey(
        UptimeBatch, related_name='regular_checks')
    date_checked = models.DateTimeField(default=timezone.now)
    total_posts = models.IntegerField(default=0)
    new_posts = models.IntegerField(default=0)
    signature_found = models.BooleanField(default=True)
    status_code = models.IntegerField()
    initial = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    def get_new_posts(self):
        if self.initial:
            fp_batches = self.forum_profile.uptime_batches.all().order_by('-date_started')
            fp_batches_ids = [x.id for x in fp_batches]
            target_index = fp_batches_ids.index(self.uptime_batch.id)
            if fp_batches.count() > 1:
                prev_batch = fp_batches[target_index - 1]
                return self.new_posts - prev_batch.get_total_posts_with_sig(latest_only=False)
            else:
                return self.new_posts
        else:
            return self.new_posts

    def save(self, *args, **kwargs):
            batches = self.forum_profile.uptime_batches.all()
            new_batch_created = False
            save_this_check = True
            carry_over_posts = 0
            deleted_posts = 0
            if self._state.adding is True:
                if self.status_code == 200:
                    # Automatically assign to old or new uptime batch
                    if batches.filter(active=True).count():
                        latest_batch = batches.last()
                        if self.signature_found:
                            # Check if the latest batch is closed
                            if latest_batch.active:
                                if latest_batch.regular_checks.count():
                                    # Check if the number of posts has levelled out with or gone below
                                    # the last check for this batch
                                    earliest_batch = batches.first()
                                    earliest_check = earliest_batch.regular_checks.first()
                                    latest_check = latest_batch.regular_checks.last()
                                    latest_total = latest_check.total_posts
                                    diff = int(self.total_posts) - \
                                        int(latest_total)
                                    if latest_batch.regular_checks.count() > 1:
                                        if diff < 0:
                                            if latest_batch.get_total_posts_with_sig(latest_only=False):
                                                # Open a new batch for this
                                                batch = UptimeBatch(
                                                    forum_profile=self.forum_profile)
                                                batch.save()
                                                # We can’t detect which specific posts are deleted
                                                # (either old or new) so we always assume that the
                                                # deleted posts have always had signature
                                                # So, we report as new posts the posts with sig
                                                # in previous batch minus the deleted posts
                                                # Reason: Read the `Why carry over new posts count?` in 
                                                # this model's docs
                                                reg_checks = latest_batch.regular_checks.all()
                                                last_psts_wsig = [
                                                    x.new_posts for x in reg_checks]
                                                self.new_posts = 0
                                                if last_psts_wsig:
                                                    adj_new_posts = sum(last_psts_wsig) - abs(diff)
                                                    if adj_new_posts > 0:
                                                        self.new_posts = adj_new_posts
                                                self.uptime_batch = batch
                                                self.initial = True
                                                # Close the current batch
                                                latest_batch.active = False
                                                latest_batch.date_ended = timezone.now()
                                                latest_batch.reason_closed = 'post_deletion'
                                                # You can't delete more than the diff of posts between
                                                # the earliest check and latest check
                                                if self.total_posts >= earliest_check.total_posts:
                                                    latest_batch.num_deleted_posts = abs(
                                                        diff)
                                                latest_batch.save()
                                                # Overwrite the deleted_posts variable
                                                deleted_posts = abs(diff)
                                                # Overwrite the carry_over_posts variable
                                                carry_over_posts = sum(last_psts_wsig)
                                            else:
                                                self.uptime_batch = latest_batch
                                        else:
                                            self.uptime_batch = latest_batch
                                    else:
                                        self.uptime_batch = latest_batch
                                else:
                                    self.uptime_batch = latest_batch
                                    self.initial = True
                            else:
                                # Detect if post deletion happened
                                total_diff = self.total_posts 
                                total_diff -= latest_batch.get_total_posts()
                                # Compute the new posts
                                new_posts = latest_batch.get_total_posts_with_sig(latest_only=False) 
                                new_posts += total_diff
                                self.new_posts = new_posts
                                # Create a new batch
                                batch = UptimeBatch(
                                    forum_profile=self.forum_profile)
                                batch.save()
                                new_batch_created = True
                                self.uptime_batch = batch
                                self.initial = True
                        else:
                            latest_batch.reason_closed = 'signature_removal'
                            # Close the current batch
                            latest_batch.active = False
                            latest_batch.date_ended = timezone.now()
                            latest_batch.save()
                            self.uptime_batch = latest_batch
                    else:
                        # No active batch exists
                        latest_batch = batches.last()
                        if self.signature_found:
                            # If the signature is found, create a new batch
                            batch = UptimeBatch(forum_profile=self.forum_profile)
                            batch.save()
                            new_batch_created = True
                            self.uptime_batch = batch
                            self.initial = True
                            # If a previous inactive batch exists,
                            # carry over the posts with sig count from it and
                            # add set as new_posts for this check
                            # Reason: Read the `Why carry over new posts count?` in this model's docs
                            if latest_batch:
                                carry_over_posts = latest_batch.get_total_posts_with_sig(latest_only=False)
                                self.new_posts += carry_over_posts
                        else:
                            # What goes here are signature checks that did not find
                            # the signature in the profile page and where there is no
                            # active uptime batch in the forum profile. We ignore this check,
                            # we're not saving this to the database
                            save_this_check = False
            if save_this_check:
                super(SignatureCheck, self).save(*args, **kwargs)
                if not new_batch_created:
                    latest_batch = batches.last()
                    # Compute the number of new posts in this check
                    checks_ids = latest_batch.regular_checks.all().order_by(
                        'id').values_list('id', flat=True)
                    if len(checks_ids) > 1:
                        previous_check_index = list(checks_ids).index(int(self.id)) - 1
                        if previous_check_index > -1:
                            previous_check_id = checks_ids[previous_check_index]
                            previous_check = SignatureCheck.objects.get(
                                id=previous_check_id)
                            new_posts = int(self.total_posts) - \
                                int(previous_check.total_posts)
                            # assign to self.new_posts
                            self.new_posts = new_posts
                            if new_posts > 0:
                                SignatureCheck.objects.filter(
                                    id=self.id).update(new_posts=new_posts)
                if latest_batch:
                    # Compare this to initial value and flag this as initial
                    # if total posts is equal or below the real initial
                    # check for this batch
                    init_check = latest_batch.regular_checks.filter(
                        initial=True).last()
                    if init_check:
                        sc = SignatureCheck.objects.get(id=self.id)
                        if sc.total_posts <= init_check.total_posts:
                            SignatureCheck.objects.filter(
                                id=self.id).update(initial=True)
                # Assign points on the cumulative point system
                # Post additions
                actual_new_posts = self.new_posts - carry_over_posts
                post_add_points = actual_new_posts * config.POINTS_NEW_POST
                if post_add_points > 0:
                    sig_points = SignaturePoints(
                        category='post_addition',
                        forum_profile=self.forum_profile,
                        uptime_batch=self.uptime_batch,
                        signature_check_id=self.id,
                        posts_count=actual_new_posts,
                        points=post_add_points
                    )
                    sig_points.save()
                # Post deletions
                post_del_points = deleted_posts * config.POINTS_DELETED_POST
                if post_del_points > 0:
                    sig_points = SignaturePoints(
                        category='post_deletion',
                        forum_profile=self.forum_profile,
                        uptime_batch=self.uptime_batch,
                        signature_check_id=self.id,
                        posts_count=deleted_posts,
                        points=post_del_points
                    )
                    sig_points.save()
                # Posts uptime
                # Read more here: `How do we assign points for post uptime?` 
                # in the docs of the SignaturePoints model
                for check in self.uptime_batch.regular_checks.filter(new_posts__gt=0):
                    latest_pts = SignaturePoints.objects.filter(signature_check_id=self.id)
                    if latest_pts.last():
                        latest_pts = latest_pts.last()
                        time_diff = timezone.now() - latest_pts.timestamp
                        hours = time_diff.total_seconds() / 3600
                        points = hours * config.POINTS_POST_UPTIME
                    else:
                        points = 0
                    sig_points = SignaturePoints(
                        category='post_uptime',
                        forum_profile=self.forum_profile,
                        uptime_batch=self.uptime_batch,
                        signature_check_id=check.id,
                        posts_count=check.new_posts,
                        points=points
                    )
                    sig_points.save()


class PointsCalculation(models.Model):
    """ Results of calculations of points for the given signature check in an uptime batch. """
    uptime_batch = models.ForeignKey(
        UptimeBatch, related_name='points_calculations')
    date_calculated = models.DateTimeField(default=timezone.now)
    signature_check = models.ForeignKey(
        SignatureCheck, related_name='points_calculations')
    post_points = models.DecimalField(max_digits=12, decimal_places=4)
    post_days_points = models.DecimalField(max_digits=12, decimal_places=4)
    influence_points = models.DecimalField(max_digits=12, decimal_places=4)
    total_points = models.DecimalField(max_digits=12, decimal_places=4)

    def save(self, *args, **kwargs):
        # if self._state.adding == True:
        batch = self.uptime_batch
        latest_gs = GlobalStats.objects.last()
        # Calculate points for posts with sig
        self.post_points = 0.0
        if batch.get_total_posts_with_sig() and latest_gs.total_posts_with_sig:
            self.post_points = decimal.Decimal(
                batch.get_total_posts_with_sig() * 6000)
            self.post_points /= latest_gs.total_posts_with_sig
        # Calculate post days points
        self.post_days_points = 0.0
        if batch.get_total_days() and latest_gs.total_days:
            self.post_days_points = decimal.Decimal(
                batch.get_total_days() * 3800)
            self.post_days_points /= latest_gs.total_days
        # Calculate influence points
        self.influence_points = 0.0
        if batch.get_total_posts() and latest_gs.total_posts:
            self.influence_points = decimal.Decimal(
                batch.get_total_posts() * 200)
            self.influence_points /= latest_gs.total_posts
        # Calculate total points
        self.total_points = decimal.Decimal(self.post_points)
        self.total_points += decimal.Decimal(self.post_days_points)
        self.total_points += decimal.Decimal(self.influence_points)
        super(PointsCalculation, self).save(*args, **kwargs)

    def get_total_tokens(self):
        total_points = self.total_points
        tokens = (total_points * config.VTX_AVAILABLE) / 10000
        return round(tokens, 2)


class ScrapingError(models.Model):
    """ Record of scraping errors """
    forum = models.ForeignKey(ForumSite, related_name='scraping_errors')
    forum_profile = models.ForeignKey(
        ForumProfile, related_name='scraping_errors')
    error_type = models.CharField(max_length=30)
    traceback = models.TextField()
    resolved = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)
    date_resolved = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class DataUpdateTask(models.Model):
    """ Record details about the execution run of scraping and data update tasks """
    task_id = models.CharField(max_length=50)
    date_started = models.DateTimeField(default=timezone.now)
    success = models.NullBooleanField(null=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    scraping_errors = models.ManyToManyField(ScrapingError)

    def __str__(self):
        return str(self.id)


VARIANT_CHOICES = (
    ('primary', 'Primary'),
    ('secondary', 'Secondary'),
    ('success', 'Success'),
    ('danger', 'Danger'),
    ('warning', 'Warning'),
    ('info', 'Info')
)


class Notification(models.Model):
    code = models.CharField(max_length=20, blank=True)
    text = models.CharField(max_length=100)
    action_text = models.CharField(max_length=30, blank=True)
    action_link = models.CharField(max_length=100, blank=True)
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
