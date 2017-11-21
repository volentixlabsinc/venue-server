from venue.models import UserProfile, ForumSite, ForumProfile, Signature
from .tasks import verify_profile_signature, send_email_confirmation
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.shortcuts import render, redirect
from rest_framework.response import Response
from django.contrib.auth.models import User
from venue.tasks import get_user_position
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from constance import config
from hashids import Hashids
import json

# Instantiate a Hashids instance to be used later
hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)

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
            'user_profile_id': token.user.profiles.first().id,
            'email_confirmed': token.user.profiles.first().email_confirmed
        }
        # Update last login datetime
        token.user.last_login = timezone.now()
        token.user.save()
        return Response(data)
        
@csrf_exempt
def get_user(request):
    data = {'found': False}
    try:
        data = json.loads(request.body)
        token = Token.objects.filter(key=data['token'])
        if token.exists():
            token = token.first()
            data = {
                'found': True,
                'token': token.key, 
                'username': token.user.username, 
                'email': token.user.email,
                'email_confirmed': token.user.profiles.first().email_confirmed
            }
    except TypeError:
        pass
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
        # Send confirmation email
        code = hashids.encode(int(user.id))
        send_email_confirmation.delay(user.email, user.username, code)
    except Exception as exc:
        response['status'] = 'error'
        response['message'] = str(exc)
    return JsonResponse(response)
    
def confirm_email(request):
    code = request.GET.get('code')
    user_id, = hashids.decode(code)
    user_profile = UserProfile.objects.get(user_id=user_id)
    user_profile.email_confirmed = True
    user_profile.save()
    return redirect('/#/?email_confirmed=1')
    
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
    
@csrf_exempt
def get_site_configs(request):
    configs = {
        'disable_sign_up': config.DISABLE_SIGN_UP
    }
    return JsonResponse(configs)
    
@csrf_exempt
def get_stats(request):
    data = json.loads(request.body)
    stats = []
    token = Token.objects.get(key=data['apiToken'])
    fps = ForumProfile.objects.filter(user_profile__user=token.user)
    for fp in fps:
        fields = ['postPoints', 'postDaysPoints', 'influencePoints', 'totalPoints', 'VTX_Tokens']
        fp_data = {k: [] for k in fields}
        for batch in fp.uptime_batches.filter(active=True):
            latest_calc = batch.regular_checks.last().points_calculations.last()
            fp_data['postPoints'].append(latest_calc.post_points)
            fp_data['postDaysPoints'].append(latest_calc.post_days_points)
            fp_data['influencePoints'].append(latest_calc.influence_points)
            fp_data['totalPoints'].append(latest_calc.total_points)
            fp_data['VTX_Tokens'].append(latest_calc.get_total_tokens())
        sum_up_data = {k:  '{:,}'.format(sum(v)) for k,v in fp_data.items()}
        sum_up_data['User_ID'] = fp.forum_user_id
        sum_up_data['forumSite'] = fp.forum.name
        stats.append(sum_up_data)
    return JsonResponse({'status': 'success', 'stats': stats})