"""volentix URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from venue.views import (
    frontend_app, get_user, create_user, check_profile,
    save_signature, get_site_configs, get_stats, confirm_email,
    delete_account, change_email, change_username, change_password,
    authenticate, reset_password, get_leaderboard_data, get_signature_code,
    change_language, check_email_exists, check_username_exists,
    get_languages, generate_2fa_uri, verify_2fa_code, disable_2fa,
    get_notifications, dismiss_notification, create_forum_profile,
    get_forum_sites, get_forum_profiles, get_signatures, get_points_breakdown
)
from rest_framework.documentation import include_docs_urls
from django.views.static import serve
from django.conf.urls import url
from django.conf import settings
from django.contrib import admin


urlpatterns = [
    url(r'^$', frontend_app),
    url(r'^admin/', admin.site.urls),

    url(r'^docs/', include_docs_urls(
        title='Volentix Venue API',
        permission_classes=[]
    )),

    url(r'^api/authenticate/', authenticate),

    url(r'^api/create/signature/', save_signature),
    url(r'^api/create/user/', create_user),
    url(r'^api/create/forum-profile/', create_forum_profile),

    url(r'^api/check/profile/', check_profile),
    url(r'^api/check/email-exists/', check_email_exists),
    url(r'^api/check/username-exists/', check_username_exists),

    url(r'^api/retrieve/user/', get_user),
    url(r'^api/retrieve/signature-code/', get_signature_code),
    url(r'^api/retrieve/site-configs/', get_site_configs),
    url(r'^api/retrieve/stats/', get_stats),
    url(r'^api/retrieve/languages/', get_languages),
    url(r'^api/retrieve/leaderboard-data/', get_leaderboard_data),
    url(r'^api/retrieve/notifications/', get_notifications),
    url(r'^api/retrieve/forum-sites/', get_forum_sites),
    url(r'^api/retrieve/forum-profiles/', get_forum_profiles),
    url(r'^api/retrieve/signatures/', get_signatures),
    url(r'^api/retrieve/points-breakdown/', get_points_breakdown),

    url(r'^api/manage/confirm-email', confirm_email),
    url(r'^api/manage/change-email/', change_email),
    url(r'^api/manage/change-language/', change_language),
    url(r'^api/manage/reset-password/', reset_password),
    url(r'^api/manage/change-password/', change_password),
    url(r'^api/manage/enable-two-factor-auth', generate_2fa_uri),
    url(r'^api/manage/change-username/', change_username),
    url(r'^api/manage/delete-account/', delete_account),
    url(r'^api/manage/verify-otp-code/', verify_2fa_code),
    url(r'^api/manage/disable-two-factor-auth/', disable_2fa),
    url(r'^api/manage/dismiss-notification/', dismiss_notification)
]


if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT
        }),
        url(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT
        })
    ]
