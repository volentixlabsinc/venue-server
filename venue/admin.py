from venue.models import (
    ForumSite, Signature, UserProfile, ForumProfile,
    UptimeBatch, SignatureCheck, PointsCalculation, Language,
    GlobalStats, ForumUserRank, DataUpdateTask, ScrapingError,
    Ranking, Notification, SignaturePoints
)
from django.contrib.admin import SimpleListFilter
from django.contrib import admin


# ---------------
# Custom filters
# ---------------


class FieldForumProfileFilter(SimpleListFilter):
    title = 'active_forum_profile'
    parameter_name = 'forum_profile'

    def lookups(self, request, model_admin):
        forum_profiles = set([x.forum_profile for x in model_admin.model.objects.all()])
        return [(x.id, str(x)) for x in forum_profiles]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(forum_profile_id=self.value())
        else:
            return queryset.all()


# Customize the titles in the headers and index template
admin.site.site_title = 'Volentix Venue Administration'
admin.site.site_header = 'Volentix Venue Administration'
admin.site.index_title = 'Apps and Data'
admin.site.index_template = 'admin/custom_index.html'

admin.site.register(ForumSite)
admin.site.register(Signature)


class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'active']


admin.site.register(Language, LanguageAdmin)


class RankingAdmin(admin.ModelAdmin):
    list_display = ['username', 'rank', 'ranking_date']

    def username(self, obj):
        return obj.user_profile.user.username


admin.site.register(Ranking, RankingAdmin)


class ScrapingErrorAdmin(admin.ModelAdmin):
    list_display = ['error_type', 'forum_profile', 'date_created']
    

admin.site.register(ScrapingError, ScrapingErrorAdmin)


class UptimeBatchAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'forum_profile', 'batch_number', 'total_posts',
        'total_posts_with_sig', 'total_days', 'post_points',
        'post_days_points', 'influence_points', 'active',
        'date_started', 'date_ended', 'reason_closed', 'num_deleted_posts'
    ]
    list_filter = [FieldForumProfileFilter, 'forum_profile__user_profile']
    
    def user(self, obj):
        return obj.forum_profile.user_profile.user.username
        
    def forum_profile(self, obj):
        return obj.forum_profile
        
    def batch_number(self, obj):
        return obj.get_batch_number()
        
    def total_posts(self, obj):
        return obj.get_total_posts()
        
    def total_posts_with_sig(self, obj):
        return obj.get_total_posts_with_sig()
        
    def total_days(self, obj):
        return obj.get_total_days()
        
    def post_points(self, obj):
        return obj.get_post_points()
        
    def post_days_points(self, obj):
        return obj.get_post_days_points()
        
    def influence_points(self, obj):
        return obj.get_influence_points()
    

admin.site.register(UptimeBatch, UptimeBatchAdmin)


class PointsCalculationAdmin(admin.ModelAdmin):
    list_display = ['id', 'uptime_batch', 'forum_profile', 'user', 'signature_check', 'post_points', 
        'post_days_points', 'influence_points', 'date_calculated']
    list_filter = ['uptime_batch__forum_profile', 'uptime_batch__forum_profile__user_profile']
        
    def user(self, obj):
        return obj.uptime_batch.forum_profile.user_profile.user.username
    
    def forum_profile(self, obj):
        return obj.uptime_batch.forum_profile
        

admin.site.register(PointsCalculation, PointsCalculationAdmin)


class GlobalStatsAdmin(admin.ModelAdmin):
    list_display = [
        'total_posts', 'total_posts_with_sig', 'total_days',
        'date_updated'
    ]
    

admin.site.register(GlobalStats, GlobalStatsAdmin)


class SignatureCheckAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'forum_profile', 'uptime_batch', 'total_posts',
        'new_posts', 'signature_found', 'date_checked'
    ]
    list_filter = [FieldForumProfileFilter, 'forum_profile__user_profile']

    def user(self, obj):
        return obj.uptime_batch.forum_profile.user_profile.user.username

    def forum_profile(self, obj):
        return obj.uptime_batch.forum_profile


admin.site.register(SignatureCheck, SignatureCheckAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = 'admin/userprofile_change_list.html'
    list_display = [
        'user', 'total_posts', 'total_posts_with_sig',
        'total_post_days', 'total_points', 'total_tokens'
    ]
    search_fields = ['user__username']

    def changelist_view(self, request, extra_context=None):
        user_profiles = UserProfile.objects.all()
        sum_posts = sum([float(x.get_total_posts()) for x in user_profiles])
        sum_posts_with_sig = sum([float(x.get_total_posts_with_sig()) for x in user_profiles])
        sum_post_days = sum([float(x.get_total_days()) for x in user_profiles])
        sum_points = sum([float(x.get_total_points()) for x in user_profiles])
        sum_vtx = sum([float(x.get_total_tokens()) for x in user_profiles])
        dashboard_cards = [
            {'name': 'Total Users', 'value': user_profiles.count()},
            {'name': 'Total Posts', 'value': int(sum_posts)},
            {'name': 'Total Posts With Sig', 'value': int(sum_posts_with_sig)},
            {'name': 'Total Post Days', 'value': round(sum_post_days, 2)},
            {'name': 'Total Points', 'value': int(sum_points)},
            {'name': 'Total VTX', 'value': int(round(sum_vtx, 0))}
        ]
        response = super().changelist_view(
            request,
            extra_context={'dashboard_cards': dashboard_cards},
        )
        return response

    def total_posts(self, obj):
        return obj.get_total_posts()

    def total_posts_with_sig(self, obj):
        return obj.get_total_posts_with_sig()

    def total_post_days(self, obj):
        return round(obj.get_total_days(), 4)

    def total_points(self, obj):
        return round(obj.get_total_points(), 2)

    def total_tokens(self, obj):
        return obj.get_total_tokens()


admin.site.register(UserProfile, UserProfileAdmin)


class ForumUserRankAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum_site', 'allowed']
    list_filter = ['forum_site']


admin.site.register(ForumUserRank, ForumUserRankAdmin)


class ForumProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_profile', 'forum', 'forum_user_id', 'forum_username',
        'forum_rank', 'verified', 'total_posts', 'total_posts_with_sig',
        'total_days'
    ]

    def total_posts(self, obj):
        return obj.get_total_posts(actual=True)

    def total_posts_with_sig(self, obj):
        return obj.get_total_posts_with_sig()

    def total_days(self, obj):
        return obj.get_total_days()


admin.site.register(ForumProfile, ForumProfileAdmin)


class DataUpdateTaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'date_started', 'success', 'date_completed', 'errors_count']

    def errors_count(self, obj):
        return obj.scraping_errors.all().count()


admin.site.register(DataUpdateTask, DataUpdateTaskAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['text', 'dismissible', 'active', 'date_created']


admin.site.register(Notification, NotificationAdmin)


class SignaturePointsAdmin(admin.ModelAdmin):
    list_display = ['user', 'forum_profile', 'category', 'points']

    def user(self, obj):
        return obj.forum_profile.user_profile


admin.site.register(SignaturePoints, SignaturePointsAdmin)
