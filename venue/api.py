from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import serializers, viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import (ForumSite, ForumProfile, Signature, UserProfile, ForumUserRank)
from .tasks import get_user_position
from rest_framework.fields import CurrentUserDefault
from django.db import IntegrityError
from rest_framework import generics
from django.utils import timezone
import re

#------------------
# User Profiles API

class UserProfileSerializer(serializers.ModelSerializer):
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

class ForumSiteSerializer(serializers.ModelSerializer):
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

class SignatureSerializer(serializers.ModelSerializer):
    user_ranks = serializers.StringRelatedField(many=True)
    
    class Meta:
        model = Signature
        fields = ('id', 'name', 'forum_site', 'user_ranks', 'code', 'image', 'active')
        
def inject_verification_code(sig_code, verification_code):
    def repl(m):
        return '%s?vcode=%s' % (m.group(), verification_code)
    if 'http' in sig_code:
        pattern = r'http[s]?://([a-z./-?=&])+'
        return re.sub(pattern, repl, sig_code)
    elif 'link' in sig_code:
        return sig_code + '?vcode=' + verification_code

class SignatureViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    
    def get_queryset(self):
        queryset = self.queryset
        # Filter the queryset according to the query parameters
        own_sigs = self.request.query_params.get('own_sigs', None)
        if own_sigs:
            my_fps = ForumProfile.objects.filter(user_profile__user=self.request.user, verified=True)
            name_map = {}
            for fp in my_fps:
                name = 'Forum site: %s / User ID: %s' % (fp.forum.name, fp.forum_user_id)
                name_map[fp.signature.id] = name
            my_sigs = my_fps.values_list('signature_id', flat=True)
            my_sigs = queryset.filter(id__in=list(my_sigs))
            for sig in my_sigs:
                sig.name = name_map[sig.id]
            return my_sigs
        else:
            forum_site_id = self.request.query_params.get('forum_site_id', None)
            forum_user_rank = self.request.query_params.get('forum_user_rank', None)
            forum_profile_id = self.request.query_params.get('forum_profile_id', None)
            forum_profile = ForumProfile.objects.get(id=forum_profile_id)
            if forum_site_id and forum_user_rank:
                queryset = queryset.filter(forum_site_id=forum_site_id, user_ranks__name=forum_user_rank)
                # Modify the links in the code so it contains the verification code
                for sig in queryset:
                    sig.code = inject_verification_code(sig.code, forum_profile.verification_code)
            return queryset
    
#-------------------
# Forum Profiles API

class ForumProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumProfile
        fields = ('id', 'profile_url', 'signature', 'forum')
        
class ForumProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = ForumProfile.objects.all()
    serializer_class = ForumProfileSerializer
    
    def get_queryset(self):
        queryset = self.queryset
        forum_id = self.request.query_params.get('forum_id', None)
        forum_user_id = self.request.query_params.get('forum_user_id', None)
        if forum_id and forum_user_id:
            queryset = queryset.filter(forum_id=forum_id, forum_user_id=forum_user_id)
        return queryset
    
    def perform_create(self, serializer):
        user_profile = UserProfile.objects.get(user=self.request.user)
        forum_id = self.request.data['forum_id']
        profile_url = self.request.data['profile_url']
        forum = ForumSite.objects.get(id=forum_id)
        info = get_user_position(forum_id, profile_url, self.request.user.id)
        profile_check = ForumProfile.objects.filter(forum_user_id=info['forum_user_id'], forum=forum)
        if profile_check.exists():
            fps = profile_check.filter(active=True, verified=True)
            fp = fps.last()
            if fp and fp.signature:
                raise serializers.ValidationError("Your profile already contains our signature.")
        else:
            rank, created = ForumUserRank.objects.get_or_create(name=info['position'], forum_site=forum)
            forum_profile = serializer.save(
                user_profile=user_profile, 
                forum_user_id=info['forum_user_id'],
                forum=forum, 
                forum_rank=rank,
                active=True)