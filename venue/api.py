from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import serializers, viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import (ForumSite, ForumProfile, Signature, UserProfile)
from rest_framework import generics

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
            
class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
#----------------
# Forum Sites API

class ForumSiteSerializer(serializers.HyperlinkedModelSerializer):
    used = serializers.BooleanField()
    
    class Meta:
        model = ForumSite
        fields = ('id', 'name', 'address', 'used')
        
class ForumSiteViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = ForumSite.objects.all()
    serializer_class = ForumSiteSerializer
    
    def get_queryset(self):
        queryset = self.queryset
        # Annotate the queryset
        user_forum_profiles = ForumProfile.objects.filter(user_profile__user=self.request.user)
        for obj in queryset:
            obj.used = user_forum_profiles.filter(forum_id=obj.id).exists()
        return queryset
    
#---------------
# Signatures API

class SignatureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Signature
        fields = ('id', 'name', 'forum_site', 'code', 'active')
        
class SignatureViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    
    def get_queryset(self):
        queryset = self.queryset
        # Annotate the queryset
        forum_site_id = self.request.query_params.get('forum_site_id', None)
        if forum_site_id:
            queryset = queryset.filter(forum_site_id=forum_site_id) 
        return queryset
    
#-------------------
# Forum Profiles API

class ForumProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForumProfile
        fields = '__all__'
        
class ForumProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = ForumProfile.objects.all()
    serializer_class = ForumProfileSerializer