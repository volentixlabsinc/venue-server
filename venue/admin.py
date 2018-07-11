from venue.models import (
    ForumSite, Signature, UserProfile, Ranking, ForumProfile,
    Language, ForumUserRank, ForumPost, Notification
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
    list_display = ['user', 'email_confirmed', 'receive_emails']


admin.site.register(UserProfile, UserProfileAdmin)


class ForumUserRankAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum_site', 'allowed', 'bonus_percentage']
    list_filter = ['forum_site']


admin.site.register(ForumUserRank, ForumUserRankAdmin)


class ForumProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_profile', 'forum', 'forum_user_id', 'forum_username',
        'forum_rank', 'verified', 'total_posts'
    ]

    def total_posts(self, obj):
        return obj.posts.count()


admin.site.register(ForumProfile, ForumProfileAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['text', 'dismissible', 'active', 'date_created']


admin.site.register(Notification, NotificationAdmin)


class ForumPostAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'forum_profile', 'message_id', 'timestamp',
        'unique_content_length', 'valid_sig_minutes', 'invalid_sig_minutes',
        'base_points', 'forum_rank', 'influence_bonus_pts', 'total_points',
        'credited', 'matured'
    ]

    def user(self, obj):
        return obj.user_profile.user.username


admin.site.register(ForumPost, ForumPostAdmin)


class RankingAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'rank', 'batch', 'timestamp']


admin.site.register(Ranking, RankingAdmin)
