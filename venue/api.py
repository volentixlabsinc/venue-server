from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import serializers, viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import (ForumSite, Signature, UserProfile)

class CustomViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    
#------------------
# User Profiles API

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    first_name = serializers.ReadOnlyField(source='user.first_name')
    last_name = serializers.ReadOnlyField(source='user.last_name')
    total_posts = serializers.ReadOnlyField(source='get_total_posts')
    total_posts_with_sig = serializers.ReadOnlyField(source='get_total_posts_with_sig')
    total_days = serializers.ReadOnlyField(source='get_total_days')
    total_points = serializers.ReadOnlyField(source='get_total_points')
    total_tokens = serializers.ReadOnlyField(source='get_total_tokens')
    
    class Meta:
        model = UserProfile
        fields = ('username', 'first_name', 'last_name', 'total_posts', 'total_posts_with_sig', 
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