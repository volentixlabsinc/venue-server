from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ForumSite

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')
        
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
class ForumSiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForumSite
        fields = ('name', 'address')
        
class ForumSiteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = ForumSite.objects.all()
    serializer_class = ForumSiteSerializer