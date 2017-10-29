from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import (ForumSite, Signature)

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')
        
class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
class ForumSiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForumSite
        fields = ('name', 'address')
        
class ForumSiteViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ForumSite.objects.all()
    serializer_class = ForumSiteSerializer
    
class SignatureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Signature
        fields = ('name', 'forum_site', 'code', 'active')
        
class SignatureViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer