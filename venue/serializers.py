from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import (ForumSite, Signature, UserProfile)

class CustomViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    
#----------
# Users API

class UserSerializer(serializers.HyperlinkedModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')
        
class UserViewSet(CustomViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
#------------------
# User Profiles API

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    total_posts = serializers.ReadOnlyField(source='get_total_posts')
    total_posts_with_sig = serializers.ReadOnlyField(source='get_total_posts_with_sig')
    total_days = serializers.ReadOnlyField(source='get_total_days')
    total_points = serializers.ReadOnlyField(source='get_total_points')
    total_tokens = serializers.ReadOnlyField(source='get_total_tokens')
    
    class Meta:
        model = UserProfile
        fields = ('user', 'total_posts', 'total_posts_with_sig', 
            'total_days', 'total_points', 'total_tokens')
            
class UserProfileViewSet(CustomViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
            
#----------------
# Forum Sites API

class ForumSiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForumSite
        fields = ('name', 'address')
        
class ForumSiteViewSet(CustomViewSet):
    queryset = ForumSite.objects.all()
    serializer_class = ForumSiteSerializer
    
#---------------
# Signatures API

class SignatureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Signature
        fields = ('name', 'forum_site', 'code', 'active')
        
class SignatureViewSet(CustomViewSet):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer