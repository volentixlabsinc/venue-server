from venue.models import ForumSite, Signature, UserProfile, ForumProfile, UptimeBatch, SignatureCheck, PointsCalculation, GlobalStats
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import User
from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = ugettext_lazy('Volentix administration')
    # Text to put in each page's <h1> (and above login form).
    site_header = ugettext_lazy('Volentix administration')
    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Apps and Data')

admin_site = MyAdminSite()

admin_site.register(User)
admin_site.register(ForumSite)
admin_site.register(Signature)

class UptimeBatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'forum_profile', 'batch_number', 'active', 'date_started', 'date_ended']
    
    def user(self, obj):
        return obj.forum_profile.user_profile.user.username
        
    def forum_profile(self, obj):
        return obj.forum_profile
        
    def batch_number(self, obj):
        return obj.get_batch_number()
    
admin_site.register(UptimeBatch, UptimeBatchAdmin)

class PointsCalculationAdmin(admin.ModelAdmin):
    list_display = ['uptime_batch', 'signature_check', 'post_points', 
        'post_days_points', 'influence_points', 'date_calculated']
        
admin_site.register(PointsCalculation, PointsCalculationAdmin)

class GlobalStatsAdmin(admin.ModelAdmin):
    list_display = ['total_posts', 'total_posts_with_sig', 'total_days', 'date_updated']
    
admin_site.register(GlobalStats, GlobalStatsAdmin)

class SignatureCheckAdmin(admin.ModelAdmin):
    list_display = ['user', 'forum_profile', 
        'uptime_batch', 'total_posts', 'signature_found', 'date_checked']
        
    def user(self, obj):
        return obj.uptime_batch.forum_profile.user_profile.user.username
        
    def forum_profile(self, obj):
        return obj.uptime_batch.forum_profile
    
admin_site.register(SignatureCheck, SignatureCheckAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_posts', 'total_posts_with_sig', 
        'total_post_days', 'total_points', 'total_tokens']
        
    def total_posts(self, obj):
        return obj.get_total_posts()
        
    def total_posts_with_sig(self, obj):
        return obj.get_total_posts_with_sig()
        
    def total_post_days(self, obj):
        return obj.get_total_days()
        
    def total_points(self, obj):
        return obj.get_total_points()
        
    def total_tokens(self, obj):
        return obj.get_total_tokens()
        
admin_site.register(UserProfile, UserProfileAdmin)

class ForumProfileAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'forum', 'forum_user_id']
    
admin_site.register(ForumProfile, ForumProfileAdmin)