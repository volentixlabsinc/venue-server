from venue.models import UserProfile, ForumSite, ForumProfile, Signature
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from .tasks import verify_profile_signature
from rest_framework.response import Response
from django.contrib.auth.models import User
from venue.tasks import get_user_position
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
import json

def frontend_app(request):
    return render(request, 'index.html')
    
class CustomObtainAuthToken(ObtainAuthToken):
    authentication_classes = (TokenAuthentication,)
    
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        data = {
            'token': token.key, 
            'username': token.user.username, 
            'email': token.user.email,
            'user_profile_id': token.user.profiles.first().id 
        }
        return Response(data)
        
@csrf_exempt
def get_user(request):
    data = json.loads(request.body)
    token = Token.objects.filter(key=data['token'])
    if token.exists():
        token = token.first()
        data = {
            'found': True,
            'token': token.key, 
            'username': token.user.username, 
            'email': token.user.email
        }
    else:
        data = {'found': False}
    return JsonResponse(data)
    
@csrf_exempt
def create_user(request):
    data = json.loads(request.body)
    user_check = User.objects.filter(email=data['email'])
    response = {}
    try:
        if user_check.exists():
            response['status'] = 'exists'
            user = user_check.first()
        else:
            user = User.objects.create_user(**data)
            response['status'] = 'created'
        token = Token.objects.create(user=user)
        user_data = {
            'username': user.username,
            'email': user.email,
            'token': token.key
        }
        response['user'] = user_data
        user_profile = UserProfile(user=user)
        user_profile.save()
    except Exception as exc:
        response['status'] = 'error'
        response['message'] = exc.msg
    return JsonResponse(response)
    
@csrf_exempt
def check_profile(request):
    data = json.loads(request.body)
    forum = ForumSite.objects.get(id=data['forum'])
    response = {'found': False, 'forum_id': data['forum']}
    info = get_user_position(forum.id, data['profile_url'], request.user.id)
    if info['status_code'] == 200 and info['position']:
        response['position'] = info['position']
        response['forum_user_id'] = info['forum_user_id']
        response['found'] = True
        response['exists'] = info['exists']
        if info['exists']:
            response['verified'] = info['verified']
            response['own'] = info['own']
            response['with_signature'] = info['with_signature']
            response['forum_profile_id'] = info['forum_profile_id']
    response['status_code'] = info['status_code']
    return JsonResponse(response)
    
@csrf_exempt
def save_signature(request):
    data = json.loads(request.body)
    forum_profile = ForumProfile.objects.get(id=data['forum_profile_id'])
    signature = Signature.objects.get(id=data['signature_id'])
    forum_profile.signature = signature
    forum_profile.save()
    response = {'success': True}
    verified = verify_profile_signature(forum_profile.forum.id, forum_profile.id, signature.id)
    if verified:
        forum_profile.verified = True
        forum_profile.date_verified = timezone.now()
        forum_profile.save()
    else:
        response['success'] = False
        response['message'] = 'The signature could not be found in the profile page.'
    return JsonResponse(response)