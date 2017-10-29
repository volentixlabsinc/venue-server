from venue.models import (
    ForumSite, Signature, UserProfile, ForumProfile, 
    UptimeBatch, SignatureCheck, PointsCalculation, 
    GlobalStats, DataUpdateTask, ScrapingError
)
from django.contrib import admin

# Customize the titles in the headers
admin.site.site_title = 'Volentix administration'
admin.site.site_header = 'Volentix administration'
admin.site.index_title = 'Apps and Data'

admin.site.register(ForumSite)
admin.site.register(Signature)

class ScrapingErrorAdmin(admin.ModelAdmin):
    list_display = ['error_type', 'forum_profile', 'date_created']
    
admin.site.register(ScrapingError, ScrapingErrorAdmin)

class UptimeBatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'forum_profile', 'batch_number', 'active', 'date_started', 'date_ended']
    
    def user(self, obj):
        return obj.forum_profile.user_profile.user.username
        
    def forum_profile(self, obj):
        return obj.forum_profile
        
    def batch_number(self, obj):
        return obj.get_batch_number()
    
admin.site.register(UptimeBatch, UptimeBatchAdmin)

class PointsCalculationAdmin(admin.ModelAdmin):
    list_display = ['uptime_batch', 'signature_check', 'post_points', 
        'post_days_points', 'influence_points', 'date_calculated']
        
admin.site.register(PointsCalculation, PointsCalculationAdmin)

class GlobalStatsAdmin(admin.ModelAdmin):
    list_display = ['total_posts', 'total_posts_with_sig', 'total_days', 'date_updated']
    
admin.site.register(GlobalStats, GlobalStatsAdmin)

class SignatureCheckAdmin(admin.ModelAdmin):
    list_display = ['user', 'forum_profile', 
        'uptime_batch', 'total_posts', 'signature_found', 'date_checked']
        
    def user(self, obj):
        return obj.uptime_batch.forum_profile.user_profile.user.username
        
    def forum_profile(self, obj):
        return obj.uptime_batch.forum_profile
    
admin.site.register(SignatureCheck, SignatureCheckAdmin)

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
        
admin.site.register(UserProfile, UserProfileAdmin)

class ForumProfileAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'forum', 'forum_user_id']
    
admin.site.register(ForumProfile, ForumProfileAdmin)

class DataUpdateTaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'date_started', 'success', 'date_completed', 'errors_count']
    
    def errors_count(self, obj):
        return obj.scraping_errors.all().count()
        
admin.site.register(DataUpdateTask, DataUpdateTaskAdmin)