from venue.models import (
    ForumSite, Signature, UserProfile, ForumProfile,
    Language, ForumUserRank, UserPostStats, PostUptimeStats,
    Notification
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
        'forum_rank', 'verified'
    ]

    def total_posts(self, obj):
        return obj.get_total_posts(actual=True)

    def total_posts_with_sig(self, obj):
        return obj.get_total_posts_with_sig()

    def total_days(self, obj):
        return obj.get_total_days()


admin.site.register(ForumProfile, ForumProfileAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['text', 'dismissible', 'active', 'date_created']


admin.site.register(Notification, NotificationAdmin)


class UserPostStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user_profile', 'forum_profile', 'num_posts',
        'is_signature_valid', 'timestamp'
    ]


admin.site.register(UserPostStats, UserPostStatsAdmin)


class PostUptimeStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user_post_stats', 'valid_sig_minutes',
        'invalid_sig_minutes', 'timestamp'
    ]


admin.site.register(PostUptimeStats, PostUptimeStatsAdmin)
