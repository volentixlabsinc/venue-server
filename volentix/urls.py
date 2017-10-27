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
from venue.views import frontend_app, get_user, CustomObtainAuthToken
from venue.serializers import UserViewSet
from django.views.static import serve
from django.conf.urls import url, include
from django.conf import settings
from venue.admin import admin_site
from rest_framework import routers

# API Routes
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^$', frontend_app),
    url(r'^admin/', admin_site.urls),
    url(r'^api/', include(router.urls)),
    url(r'^get-user/', get_user),
    url(r'^authenticate/', CustomObtainAuthToken.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

if settings.DEBUG:
    urlpatterns += [ 
        url(r'^media/(?P<path>.*)$', serve, { 'document_root': settings.MEDIA_ROOT, }),
        url(r'^static/(?P<path>.*)$', serve, { 'document_root': settings.STATIC_ROOT })
    ]