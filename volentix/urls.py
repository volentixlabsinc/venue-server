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
    save_signature, get_site_configs, get_stats, confirm_email, delete_account, 
    change_email, change_username, change_password, authenticate, reset_password,
    get_leaderboard_data
)
from venue.api import (
    ForumSiteViewSet, ForumProfileViewSet, SignatureViewSet, UserProfileViewSet
)
from django.views.static import serve
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from rest_framework import routers

# API Routes
router = routers.DefaultRouter()
router.register(r'user-profiles', UserProfileViewSet)
router.register(r'forum-sites', ForumSiteViewSet)
router.register(r'signatures', SignatureViewSet)
router.register(r'forum-profiles', ForumProfileViewSet)

urlpatterns = [
    url(r'^$', frontend_app),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(router.urls)),
    url(r'^get-user/', get_user),
    url(r'^confirm-email', confirm_email),
    url(r'^check-profile/', check_profile),
    url(r'^save-signature/', save_signature),
    url(r'^create-user/', create_user),
    url(r'^get-site-configs/', get_site_configs),
    url(r'^get-stats/', get_stats),
    url(r'^get-leaderboard-data/', get_leaderboard_data),
    url(r'^change-email/', change_email),
    url(r'^change-username/', change_username),
    url(r'^delete-account', delete_account),
    url(r'^reset-password/', reset_password),
    url(r'^change-password/', change_password),
    url(r'^authenticate/', authenticate)
]

urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    urlpatterns += [ 
        url(r'^media/(?P<path>.*)$', serve, { 'document_root': settings.MEDIA_ROOT, }),
        url(r'^static/(?P<path>.*)$', serve, { 'document_root': settings.STATIC_ROOT })
    ]