from .tasks import ( verify_profile_signature, 
    send_email_confirmation, send_deletion_confirmation, 
    send_email_change_confirmation, send_reset_password)
from venue.models import UserProfile, ForumSite, ForumProfile, Signature, ForumUserRank, UptimeBatch
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from venue.tasks import get_user_position, update_data
from rest_framework.authtoken.models import Token
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from constance import config
from hashids import Hashids
from operator import itemgetter
from .utils import RedisTemp
import json

# Instantiate a Hashids instance to be used later
hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)

@ensure_csrf_cookie
def frontend_app(request):
    return render(request, 'index.html')
    
def authenticate(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    response = {'success': False}
    try:
        if '@' in data['username']:
            user = User.objects.get(email=data['username'])
        else:
            user = User.objects.get(username=data['username'])
        token, created = Token.objects.get_or_create(user=user)
        user.last_login = timezone.now()
        user.save()
        response = {
            'success': True,
            'token': token.key, 
            'username': user.username, 
            'email': token.user.email,
            'user_profile_id': user.profiles.first().id,
            'email_confirmed': user.profiles.first().email_confirmed
        }
    except Exception as exc:
        response['message'] = str(exc)
    return JsonResponse(response)
        
def get_user(request):
    data = {'found': False}
    try:
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
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
    
def create_user(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
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
    
def check_profile(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    forum = ForumSite.objects.get(id=data['forum'])
    response = {'found': False, 'forum_id': data['forum']}
    token = Token.objects.get(key=data['apiToken'])
    info = get_user_position(forum.id, data['profile_url'], token.user.id)
    if info['status_code'] == 200 and info['position']:
        response['position'] = info['position']
        forum_rank = ForumUserRank.objects.get(forum_site=forum, name__iexact=info['position'].strip())
        response['position_allowed'] = forum_rank.allowed
        response['forum_user_id'] = info['forum_user_id']
        response['found'] = True
        response['exists'] = info['exists']
        if info['exists']:
            response['verified'] = info['verified']
            response['own'] = info['own']
            response['active'] = info['active']
            response['with_signature'] = info['with_signature']
            response['forum_profile_id'] = info['forum_profile_id']
    response['status_code'] = info['status_code']
    return JsonResponse(response)
    
def save_signature(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
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
        # Update the data for this newly verified forum profile
        job = update_data.delay(forum_profile.id)
        response['task_id'] = job.id
    else:
        response['success'] = False
        response['message'] = 'The signature could not be found in the profile page.'
    return JsonResponse(response)
    
def get_site_configs(request):
    configs = {
        'disable_sign_up': config.DISABLE_SIGN_UP
    }
    return JsonResponse(configs)
    
def get_stats(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    stats = []
    token = Token.objects.get(key=data['apiToken'])
    fps = ForumProfile.objects.filter(user_profile__user=token.user, verified=True)
    for fp in fps:
        fields = ['postPoints', 'totalPostsWithSig', 'postDaysPoints', 'totalPostDays',
            'influencePoints', 'totalPosts', 'totalPoints', 'VTX_Tokens']
        fp_data = {k: [] for k in fields}
        latest_batch = fp.uptime_batches.last()
        fp_data['totalPosts'].append(latest_batch.get_total_posts(actual=True))
        # Sum up the credits and points from all batches for this forum profiles
        for batch in fp.uptime_batches.all():
            latest_check = batch.regular_checks.last()
            latest_calc = latest_check.points_calculations.last()
            if latest_calc:
                fp_data['postPoints'].append(int(latest_calc.post_points))
                fp_data['totalPostsWithSig'].append(batch.get_total_posts_with_sig())
                fp_data['postDaysPoints'].append(int(latest_calc.post_days_points))
                fp_data['totalPostDays'].append(batch.get_total_days())
                fp_data['influencePoints'].append(int(latest_calc.influence_points))
                fp_data['totalPoints'].append(round(latest_calc.total_points, 0))
                fp_data['VTX_Tokens'].append(round(latest_calc.get_total_tokens(), 0))
        sum_up_data = {k:  '{:,}'.format(sum(v)) for k,v in fp_data.items()}
        sum_up_data['User_ID'] = fp.forum_user_id
        sum_up_data['forumSite'] = fp.forum.name
        sum_up_data['forumUserId'] = fp.forum_user_id
        sum_up_data['forumUserRank'] = fp.forum_rank.name
        sum_up_data['_showDetails'] = False
        if latest_batch.active == False:
            sum_up_data['_rowVariant'] = 'danger'
        current_branch_no = latest_batch.get_batch_number()
        sum_up_data['currentUptimeBatch'] = {}
        if fp.uptime_batches.count() > 1:
            sum_up_data['hasPreviousBatches'] = True
            sum_up_data['previousBatches'] = []
        for item in fp.uptime_batches.all():
            batch_no = item.get_batch_number()
            data = {
                'batch': batch_no,
                'totalPostsWithSig': item.get_total_posts_with_sig(),
                'totalPostDays': item.get_total_days()
            }
            if batch_no == current_branch_no:
                sum_up_data['currentUptimeBatch'] = data
            else:
                sum_up_data['previousBatches'].append(data)
        stats.append(sum_up_data)
    return JsonResponse({'status': 'success', 'stats': stats})
    
def delete_account(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        token = Token.objects.get(key=data['apiToken'])
        code = hashids.encode(int(token.user.id))
        send_deletion_confirmation.delay(token.user.email, token.user.username, code)
    elif request.method == 'GET':
        code = request.GET.get('code')
        if code:
            user_id, = hashids.decode(code)
            User.objects.filter(id=user_id).delete()
    return redirect('/#/?account_deleted=1')
    
def change_email(request):
    rtemp = RedisTemp('new_email')
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        token = Token.objects.get(key=data['apiToken'])
        response = {'success': False}
        email_check = User.objects.filter(email=data['email'])
        if email_check.exists():
            response['message'] = 'Email already exists'
        else:
            code = hashids.encode(int(token.user.id))
            rtemp.store(code, data['email'])
            send_email_change_confirmation.delay(data['email'], token.user.username, code)
            response['success'] = True
        return JsonResponse(response)
    elif request.method == 'GET':
        code = request.GET.get('code')
        if code:
            user_id, = hashids.decode(code)
            new_email = rtemp.retrieve(code)
            User.objects.filter(id=user_id).update(email=new_email)
            rtemp.remove(code)
        return redirect('/#/settings/?updated_email=1')
        
def change_username(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        token = Token.objects.get(key=data['apiToken'])
        response = {'success': False}
        username_check = User.objects.filter(username=data['username'])
        if username_check.exists():
            response['message'] = 'Username already exists'
        else:
            User.objects.filter(id=token.user_id).update(username=data['username'])
            response['success'] = True
            response['username'] = token.user.username
            response['email'] = token.user.email
        return JsonResponse(response)
        
def change_password(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        token = Token.objects.get(key=data['apiToken'])
        response = {'success': False}
        try:
            user = User.objects.get(id=token.user_id)
            user.set_password(data['password'])
            user.save()
            response['success'] = True
        except Exception as exc:
            response['message'] = str(exc)
        return JsonResponse(response)
        
def reset_password(request):
    response = {'success': False}
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        if data['action'] == 'trigger':
            user = User.objects.get(email=data['email'])
            code = hashids.encode(int(user.id))
            send_reset_password.delay(user.email, user.username, code)
            response['success'] = True
        elif data['action'] == 'set_password':
            user_id, = hashids.decode(data['code'])
            user = User.objects.get(id=user_id)
            user.set_password(data['password'])
            user.save()
            response['success'] = True
        return JsonResponse(response)
        
def get_leaderboard_data(request):
    response = {'success': False}
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    token_check = Token.objects.filter(key=data['token'])
    if token_check.exists():
        user_profiles = UserProfile.objects.all()
        leaderboard_data = []
        for user_profile in user_profiles:
            user_data = {}
            user_data['username'] = user_profile.user.username
            user_data['tokens'] = int(user_profile.get_total_tokens())
            leaderboard_data.append(user_data)
        # Order according to amount of tokens
        leaderboard_data = sorted(leaderboard_data, key=itemgetter('tokens'), reverse=True)
        response['data'] = leaderboard_data
        response['success'] = True
    return JsonResponse(response)
