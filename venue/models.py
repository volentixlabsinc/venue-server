from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from constance import config

class ForumSite(models.Model):
    """ Forum site names and addresses """
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    scraper_name = models.CharField(max_length=30)
    
    def __str__(self):
        return self.name

class Signature(models.Model):
    """ Signature types per forum site """
    name = models.CharField(max_length=30)
    forum_site = models.ForeignKey(ForumSite, related_name='signature_types')
    code = models.TextField()
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """ Custom internal user profiles """
    user = models.ForeignKey(User)
    
    def __str__(self):
        return self.user.username
        
    def get_total_posts(self):
        total_per_forum = []
        for site in self.forum_profiles.all():
            latest_batch = site.uptime_batches.latest('date_started')
            if latest_batch.active:
                total_per_forum.append(latest_batch.get_total_posts())
        return sum(total_per_forum)
        
    def get_total_posts_with_sig(self):
        total_per_forum = []
        for site in self.forum_profiles.all():
            latest_batch = site.uptime_batches.latest('date_started')
            if latest_batch.active:
                total_per_forum.append(latest_batch.get_total_posts_with_sig())
        return sum(total_per_forum)
        
    def get_total_days(self):
        total_per_forum = []
        for site in self.forum_profiles.all():
            latest_batch = site.uptime_batches.latest('date_started')
            if latest_batch.active:
                total_per_forum.append(latest_batch.get_total_days())
        return sum(total_per_forum)
        
    def get_total_points(self):
        total_per_forum = []
        for site in self.forum_profiles.all():
            for batch in site.uptime_batches.all():
                uptime_points = batch.get_total_points()
                total_per_forum.append(uptime_points)
        return sum(total_per_forum)
        
    def get_total_tokens(self):
        total_points = self.get_total_points()
        tokens = (total_points * config.VTX_AVAILABLE) / 10000
        return int(tokens)

class ForumProfile(models.Model):
    """ Record of forum profile details per user """
    user_profile = models.ForeignKey(UserProfile, related_name='forum_profiles')
    forum = models.ForeignKey(ForumSite, null=True, blank=True, related_name='users')
    forum_user_id = models.CharField(max_length=50)
    signature = models.ForeignKey(Signature, null=True, blank=True, related_name='users')
    date_joined = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return '%s %s' % (self.forum_user_id, self.forum.name)

class GlobalStats(models.Model):
    """ Records the sitewide or global stats """
    total_posts = models.IntegerField()
    total_posts_with_sig = models.IntegerField()
    total_days = models.IntegerField()
    date_updated = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = 'Global stats'

class UptimeBatch(models.Model):
    """ Grouping of calculation results into periods of continuous uptime """
    forum_profile = models.ForeignKey(ForumProfile, related_name='uptime_batches')
    date_started = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    date_ended = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Uptime batches'
        
    def __str__(self):
        return str(self.id)
        
    def get_total_posts(self):
        latest_check = self.regular_checks.latest('date_checked')
        return latest_check.total_posts
        
    def get_total_posts_with_sig(self):
        earliest_check = self.regular_checks.earliest('date_checked')
        latest_check = self.regular_checks.latest('date_checked')
        earliest_total = earliest_check.total_posts
        latest_total = latest_check.total_posts
        return latest_total - earliest_total
        
    def get_total_days(self):
        earliest_check = self.regular_checks.earliest('date_checked')
        latest_check = self.regular_checks.latest('date_checked')
        earliest_check_date = earliest_check.date_checked
        latest_check_date = latest_check.date_checked
        tdiff = latest_check_date - earliest_check_date
        days = tdiff.total_seconds() / 86400 # converts total seconds to days
        return round(days, 2)
        
    def get_total_points(self):
        latest_calc = self.points_calculations.latest('date_calculated')
        return latest_calc.total_points
        
    def get_first_check(self):
        return self.regular_checks.first()

class SignatureCheck(models.Model):
    """ Results of regular scraping from forum profile pages """
    uptime_batch = models.ForeignKey(UptimeBatch, related_name='regular_checks')
    date_checked = models.DateTimeField(default=timezone.now)
    total_posts = models.IntegerField(default=0)
    signature_found = models.BooleanField(default=True)

class PointsCalculation(models.Model):
    """ Results of calculations of points for the given uptime batch.
    The calculations are cumulative,which means that the latest row  """
    uptime_batch = models.ForeignKey(UptimeBatch, related_name='points_calculations')
    date_calculated = models.DateTimeField(default=timezone.now)
    signature_check = models.OneToOneField(SignatureCheck)
    post_points = models.FloatField()
    post_days_points = models.FloatField()
    influence_points = models.FloatField()
    total_points = models.FloatField()
    
    def save(self, *args, **kwargs):
        if not self.pk:
            sigcheck = self.signature_check
            batch = self.uptime_batch
            latest_gs = GlobalStats.objects.latest('date_updated')
            self.post_points = (batch.get_total_posts_with_sig() * 6000) / latest_gs.total_posts_with_sig
            self.post_days_points = (batch.get_total_days() * 3800) / latest_gs.total_days
            self.influence_points = (batch.get_total_posts() * 200) / latest_gs.total_posts
            self.total_points = self.post_points + self.post_days_points + self.influence_points
        super(PointsCalculation, self).save(*args, **kwargs)

class ScrapeRun(models.Model):
    """ Record details about the execution run of scrapers """
    date_started = models.DateTimeField(default=timezone.now)
    forum_site = models.ForeignKey(ForumSite, related_name='scrape_runs')
    success = models.BooleanField(default=True)
    date_completed = models.DateTimeField(default=timezone.now)
    traceback = models.TextField()