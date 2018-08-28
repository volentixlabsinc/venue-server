from django.http import HttpResponseRedirect

from venue.models import (
    ForumSite, Signature, UserProfile, Ranking, ForumProfile,
    ForumUserRank, ForumPost, Notification, Campaign
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


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_confirmed', 'receive_emails', 'user_email']
    fields = ['user', 'language', 'otp_secret',
              'enabled_2fa', 'email_confirmed',
              'receive_emails', 'user_email']
    change_list_template = 'admin/userprofile_change_list.html'
    readonly_fields = ('user_email', )

    def get_urls(self):
        from functools import update_wrapper
        from django.conf.urls import url
        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        urlpatterns = [
            url(r'^clean-campaigns-data/$', wrap(self.clean_campaigns_data), name='clean-campaigns-data'),
        ]
        return urlpatterns + urls

    def clean_campaigns_data(self, request):
        ForumPost.objects.all().delete()
        Ranking.objects.all().delete()

        self.message_user(request, "Campaigns data is cleaned up")
        return HttpResponseRedirect("../")


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
        'user', 'forum_profile', 'post_link', 'timestamp',
        'unique_content_length', 'valid_sig_minutes', 'invalid_sig_minutes',
        'base_points', 'forum_rank', 'influence_bonus_pts', 'total_points',
        'credited', 'matured', 'monitoring'
    ]
    ordering = ['-timestamp']

    # list_filter = ['forum_profile__user_profile__user']

    def post_link(self, obj):
        forum_site = obj.forum_profile.forum.name
        if 'bitcointalk' in forum_site.lower():
            args = (obj.topic_id, obj.message_id, obj.message_id)
            url = 'https://bitcointalk.org/index.php?topic=%s.msg%s#msg%s' % args
            return '<a href="%s" target="_blank">%s</a>' % (url, obj.message_id)
        else:
            return obj.message_id

    post_link.allow_tags = True

    def user(self, obj):
        return obj.user_profile.user.username


admin.site.register(ForumPost, ForumPostAdmin)


class RankingAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'rank', 'batch', 'timestamp']


admin.site.register(Ranking, RankingAdmin)


class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_start', 'campaign_end']


admin.site.register(Campaign, CampaignAdmin)
