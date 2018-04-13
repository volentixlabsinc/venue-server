"""
Volentix VENUE
View functions
"""

import re
import pyotp
from operator import itemgetter
from datetime import timedelta
from hashids import Hashids
from constance import config
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from venue.utils import encrypt_data, decrypt_data
from django.contrib.auth.models import User
from django.conf import settings
from django.http import Http404
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, schema
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from venue.api import inject_verification_code
from rest_framework.decorators import permission_classes
from .tasks import (verify_profile_signature, get_user_position, update_data,
                    send_email_confirmation, send_deletion_confirmation,
                    send_email_change_confirmation, send_reset_password)
from .models import (UserProfile, ForumSite, ForumProfile, Notification,
                     Language, Signature, ForumUserRank)
from rest_framework.schemas import AutoSchema
from .utils import RedisTemp
import coreschema
import coreapi


# Instantiate a Hashids instance to be used later
hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)


# Function that converts points to percentages
def points_to_percentage(points, category=None):
    # categories = posts / uptime / influence / total
    total = {
        'posts': 6000,
        'uptime': 3800,
        'influence': 200,
        'total': 10000
    }
    percentage = (points / total[category]) * 100
    return round(percentage, 2)


@ensure_csrf_cookie
def frontend_app(request):
    return render(request, 'index.html')


# ==============
# API Endpoints:
# ==============


# ---------------------
# Authenticate endpoint
# ---------------------

AUTHENTICATE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'username',
            required=True,
            location='form',
            schema=coreschema.String(description='Username')
        ),
        coreapi.Field(
            'password',
            required=True,
            location='form',
            schema=coreschema.String(description='Password')
        )
    ]
)


@api_view(['POST'])
@schema(AUTHENTICATE_SCHEMA)
def authenticate(request):
    data = request.data
    response = {'success': False}
    error_code = 'unknown_error'
    try:
        if '@' in data['username']:
            user = User.objects.get(email__iexact=data['username'])
        else:
            user = User.objects.get(username__iexact=data['username'])
        pass_check = user.check_password(data['password'])
        if pass_check:
            profile = user.profiles.first()
            proceed = False
            if profile.enabled_2fa:
                if data['otpCode']:
                    secret = decrypt_data(
                        profile.otp_secret,
                        settings.SECRET_KEY
                    )
                    totp = pyotp.TOTP(secret)
                    verified = totp.verify(data['otpCode'])
                    if verified:
                        proceed = True
                    else:
                        error_code = 'wrong_otp'
                else:
                    error_code = 'otp_required'
            else:
                proceed = True
            if proceed:
                token, created = Token.objects.get_or_create(user=user)
                del created
                user.last_login = timezone.now()
                user.save()
                user_profile = user.profiles.first()
                response = {
                    'success': True,
                    'token': token.key,
                    'username': user.username,
                    'email': token.user.email,
                    'user_profile_id': user_profile.id,
                    'email_confirmed': user_profile.email_confirmed,
                    'language': user_profile.language.code
                }
        else:
            error_code = 'wrong_credentials'
    except User.DoesNotExist:
        error_code = 'wrong_credentials'
    if not response['success']:
        response['error_code'] = error_code
    return Response(response)


# -------------------------
# Get user details endpoint
# -------------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_user(request):
    data = {'found': False}
    user_profile = request.user.profiles.first()
    if user_profile:
        data = {
            'found': True,
            'username': request.user.username,
            'email': request.user.email,
            'language': user_profile.language.code,
            'email_confirmed': user_profile.email_confirmed,
            'enabled_2fa': user_profile.enabled_2fa
        }
    return Response(data)


# --------------------
# Create user endpoint
# --------------------


CREATE_USER_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'email',
            required=True,
            location='form',
            schema=coreschema.String(description='Email')
        ),
        coreapi.Field(
            'username',
            required=True,
            location='form',
            schema=coreschema.String(description='Username')
        ),
        coreapi.Field(
            'password',
            required=True,
            location='form',
            schema=coreschema.String(description='Password')
        ),
        coreapi.Field(
            'language',
            required=False,
            location='form',
            schema=coreschema.String(description='Language Code')
        )
    ]
)


@api_view(['POST'])
@schema(CREATE_USER_SCHEMA)
def create_user(request):
    data = request.data
    data['email'] = data['email'].lower()
    user_check = User.objects.filter(email=data['email'])
    response = {}
    try:
        language = data['language']
        del data['language']
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
        user_profile.language = Language.objects.get(code=language)
        user_profile.save()
        # Send confirmation email
        code = hashids.encode(int(user.id))
        send_email_confirmation.delay(user.email, user.username, code)
        response['status'] = 'success'
    except Exception as exc:
        response['status'] = 'error'
        response['message'] = str(exc)
    return Response(response)


@api_view(['GET'])
def confirm_email(request):
    code = request.query_params.get('code')
    user_id, = hashids.decode(code)
    user_profile = UserProfile.objects.get(user_id=user_id)
    user_profile.email_confirmed = True
    user_profile.save()
    return redirect('/#/?email_confirmed=1')


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def check_profile(request):
    data = request.query_params
    user = request.user
    forum = ForumSite.objects.get(id=data['forum'])
    response = {'found': False, 'forum_id': data['forum']}
    info = get_user_position(forum.id, data['profile_url'], user.id)
    if info['status_code'] == 200 and info['position']:
        response['position'] = info['position']
        forum_rank = ForumUserRank.objects.get(
            forum_site=forum,
            name__iexact=info['position'].strip()
        )
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
    return Response(response)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_profile_id',
            required=True,
            location='form',
            schema=coreschema.String(description='Forum profile ID')
        ),
        coreapi.Field(
            'signature_id',
            required=True,
            location='form',
            schema=coreschema.String(description='Signature ID')
        )
    ]
))
def save_signature(request):
    data = request.data
    forum_profile = ForumProfile.objects.get(id=data['forum_profile_id'])
    signature = Signature.objects.get(id=data['signature_id'])
    forum_profile.signature = signature
    forum_profile.save()
    response = {'success': True}
    verified = verify_profile_signature(
        forum_profile.forum.id,
        forum_profile.id,
        signature.id
    )
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
    return Response(response)


@api_view(['GET'])
def get_site_configs(request):
    configs = {
        'disable_sign_up': config.DISABLE_SIGN_UP
    }
    return Response(configs)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_stats(request):
    """
    Retrieves the stats of the user
    """
    response = {'success': False}
    # Initialize empty stats container dictionary
    stats = {'fresh': False}
    # -----------------------------------
    # Generate forum profile level stats
    # -----------------------------------
    profile_stats = []
    fps = ForumProfile.objects.filter(
        user_profile__user=request.user,
        verified=True
    )
    if fps.count():
        fps_batch_initials = 0  # Used later for userlevel stats
        for fp in fps:
            fields = [
                'postPoints', 'totalPostsWithSig', 'postDaysPoints',
                'totalPostDays', 'influencePoints', 'totalPosts',
                'totalPoints', 'VTX_Tokens'
            ]
            fp_data = {k: [] for k in fields}
            latest_batch = fp.uptime_batches.last()
            if latest_batch:
                fp_data['totalPosts'].append(
                    latest_batch.get_total_posts(actual=True)
                )
                # Sum up the credits and points from all batches for this forum profiles
                for batch in fp.uptime_batches.all():
                    latest_check = batch.regular_checks.last()
                    if latest_check:
                        # latest_calc = latest_check.points_calculations.last()
                        # if latest_calc:
                        post_points = batch.get_post_points()
                        fp_data['postPoints'].append(float(post_points))
                        psts_with_sig = batch.get_total_posts_with_sig()
                        fp_data['totalPostsWithSig'].append(psts_with_sig)
                        fp_data['totalPostDays'].append(batch.get_total_days())
                        uptime_points = batch.get_post_days_points()
                        fp_data['postDaysPoints'].append(float(uptime_points))
                        influence_points = batch.get_influence_points()
                        influence_points = float(influence_points)
                        fp_data['influencePoints'].append(influence_points)
                        total_points = batch.get_total_points()
                        fp_data['totalPoints'].append(float(total_points))
                        total_tokens = (total_points / 10000)
                        total_tokens *= config.VTX_AVAILABLE
                        fp_data['VTX_Tokens'].append(float(total_tokens))
                sum_up_data = {k:  '{:,}'.format(int(round(sum(v), 0)))
                               for k, v in fp_data.items()}
                sum_up_data['User_ID'] = fp.forum_user_id
                sum_up_data['forumSite'] = fp.forum.name
                sum_up_data['forumUserId'] = fp.forum_user_id
                sum_up_data['forumUserRank'] = fp.forum_rank.name
                sum_up_data['_showDetails'] = False
                if not latest_batch.active:
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
                        'totalPostsWithSig': item.get_total_posts_with_sig(
                            latest_only=False
                        ),
                        'totalPostDays': item.get_total_days(),
                        'reasonClosed': item.reason_closed,
                        'deletedPosts': item.num_deleted_posts
                    }
                    if batch_no == current_branch_no:
                        sum_up_data['currentUptimeBatch'] = data
                    else:
                        sum_up_data['previousBatches'].append(data)
                profile_stats.append(sum_up_data)
                # Get the initial count of posts from initial batches
                earliest_batch = fp.uptime_batches.first()
                earliest_check = earliest_batch.regular_checks.filter(initial=True).first()
                if earliest_check:
                    fps_batch_initials += earliest_check.total_posts
        stats['profile_level'] = profile_stats
        # --------------------------
        # Generate user-level stats
        # --------------------------
        userlevel_stats = {}
        # Get the date string for the last seven days
        now = timezone.now()
        days = [now - timedelta(days=x) for x in range(7)]
        days = [str(x.date()) for x in days]
        user_profile = UserProfile.objects.get(user=request.user)
        userlevel_stats['daily_stats'] = []
        # Iterate over the reversed list
        for day in days[::-1]:
            data = {}
            data['posts'] = user_profile.get_daily_new_posts(date=day)
            data['rank'] = user_profile.get_ranking(date=day)
            data['date'] = day
            userlevel_stats['daily_stats'].append(data)
        userlevel_stats['fps_batch_initials'] = fps_batch_initials
        # Post points:
        post_points = round(user_profile.get_post_points(), 0)
        userlevel_stats['post_points'] = int(post_points)
        userlevel_stats['post_points_pct'] = points_to_percentage(
            post_points,
            category='posts'
        )
        # Post uptime points:
        post_days_points = round(user_profile.get_post_days_points(), 0)
        userlevel_stats['post_days_points'] = int(post_days_points)
        userlevel_stats['post_days_points_pct'] = points_to_percentage(
            post_days_points,
            category='uptime'
        )
        # Influence points:
        influence_points = round(user_profile.get_influence_points(), 0)
        userlevel_stats['influence_points'] = int(influence_points)
        userlevel_stats['influence_points_pct'] = points_to_percentage(
            influence_points,
            category='influence'
        )
        # Total points:
        total_points = round(user_profile.get_total_points(), 0)
        userlevel_stats['total_points'] = int(total_points)
        userlevel_stats['total_points_pct'] = points_to_percentage(
            total_points,
            category='total'
        )
        # Total posts, tokens, and rank:
        total_posts = round(user_profile.get_total_posts_with_sig(), 0)
        userlevel_stats['total_posts'] = total_posts
        userlevel_stats['total_tokens'] = round(user_profile.get_total_tokens(), 0)
        userlevel_stats['overall_rank'] = user_profile.get_ranking()
        stats['user_level'] = userlevel_stats
        # -------------------------
        # Generate site-wide stats
        # -------------------------
        sitewide_stats = {}
        users = UserProfile.objects.filter(email_confirmed=True)
        users_with_fp = [x.id for x in users if x.with_forum_profile]
        total_posts = [x.get_total_posts_with_sig() for x in users]
        sitewide_stats['total_users'] = len(users_with_fp)
        sitewide_stats['total_posts'] = int(sum(total_posts))
        available_tokens = '{:,}'.format(config.VTX_AVAILABLE)
        sitewide_stats['available_tokens'] = available_tokens
        stats['sitewide'] = sitewide_stats
    else:
        stats['fresh'] = True
    # Prepare the response
    response['stats'] = stats
    response['success'] = True
    return Response(response)


@api_view(['GET'])
def get_leaderboard_data(request):
    response = {}
    user_profiles = UserProfile.objects.all()
    leaderboard_data = []
    for user_profile in user_profiles:
        if user_profile.forum_profiles.count():
            user_data = {}
            user_data['rank'] = user_profile.get_ranking()
            user_data['username'] = user_profile.user.username
            user_data['total_posts'] = user_profile.get_total_posts_with_sig()
            points = round(user_profile.get_total_points(), 0)
            user_data['total_points'] = '{:,}'.format(int(points))
            tokens = round(user_profile.get_total_tokens(), 0)
            user_data['total_tokens'] = '{:,}'.format(int(tokens))
            points = round(user_profile.get_post_points(), 0)
            user_data['post_points'] = '{:,}'.format(int(points))
            points = round(user_profile.get_post_days_points(), 0)
            user_data['uptime_points'] = '{:,}'.format(int(points))
            points = round(user_profile.get_influence_points(), 0)
            user_data['influence_points'] = '{:,}'.format(int(points))
            leaderboard_data.append(user_data)
    # Order according to amount of tokens
    if leaderboard_data:
        leaderboard_data = sorted(leaderboard_data, key=itemgetter('rank'))
        response['rankings'] = leaderboard_data
        users = UserProfile.objects.filter(email_confirmed=True)
        users_with_fp = [x.id for x in users if x.with_forum_profile]
        # Get site-wide stats
        response['sitewide'] = {
            'available_points': '10,000',
            'available_tokens': '{:,}'.format(config.VTX_AVAILABLE),
            'total_users': len(users_with_fp),
            'total_posts': int(sum([x.get_total_posts_with_sig() for x in users]))
        }
        if request.user.is_anonymous():
            response['userstats'] = {}
        else:
            user_profile = UserProfile.objects.get(user=request.user)
            total_tokens = user_profile.get_total_tokens()
            response['userstats'] = {
                'overall_rank': user_profile.get_ranking(),
                'total_tokens': int(round(total_tokens, 0))
            }

    # Generate forum stats
    forum_stats = {
        'posts': [],
        'users': []}
    sites = ForumSite.objects.all()
    colors = ['#2a96b6', '#5a2998', '#b62da9']
    for i, site in enumerate(sites):
        total_posts = 0
        fps = site.forum_profiles.filter(verified=True)
        for fp in fps:
            total_posts += fp.get_total_posts_with_sig()
        total_users = fps.count()
        forum_stats['posts'].append({
            'forumSite': site.name,
            'value': total_posts,
            'color': colors[i]
        })
        forum_stats['users'].append({
            'forumSite': site.name,
            'value': total_users,
            'color': colors[i]
        })
    response['forumstats'] = forum_stats
    response['success'] = True
    return Response(response)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        code = hashids.encode(int(user.id))
        send_deletion_confirmation.delay(
            user.email,
            user.username,
            code
        )
    elif request.method == 'GET':
        code = request.query_params.get('code')
        if code:
            user_id, = hashids.decode(code)
            User.objects.filter(id=user_id).delete()
            return redirect('/#/?account_deleted=1')
        else:
            return Response({'success': False})


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'email',
            required=True,
            location='form',
            schema=coreschema.String(description='New email')
        )
    ]
))
def change_email(request):
    rtemp = RedisTemp('new_email')
    if request.method == 'POST':
        data = request.data
        user = request.user
        response = {'success': False}
        email_check = User.objects.filter(email=data['email'])
        if email_check.exists():
            response['message'] = 'Email already exists'
        else:
            code = hashids.encode(int(user.id))
            rtemp.store(code, data['email'])
            send_email_change_confirmation.delay(
                data['email'],
                user.username,
                code
            )
            response['success'] = True
        return Response(response)
    elif request.method == 'GET':
        code = request.query_params.get('code')
        if code:
            user_id, = hashids.decode(code)
            new_email = rtemp.retrieve(code)
            User.objects.filter(id=user_id).update(email=new_email)
            rtemp.remove(code)
        return redirect('/#/settings/?updated_email=1')


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'username',
            required=True,
            location='form',
            schema=coreschema.String(description='Username')
        )
    ]
))
def change_username(request):
    data = request.data
    user = request.user
    response = {'success': False}
    username_check = User.objects.filter(username=data['username'])
    if username_check.exists():
        response['message'] = 'Username already exists'
    else:
        User.objects.filter(id=user.id).update(username=data['username'])
        response['success'] = True
        response['username'] = user.username
        response['email'] = user.email
    return Response(response)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'password',
            required=True,
            location='form',
            schema=coreschema.String(description='Password')
        )
    ]
))
def change_password(request):
    data = request.data
    response = {}
    user = User.objects.get(id=request.user.id)
    user.set_password(data['password'])
    user.save()
    response['success'] = True
    return Response(response)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'language',
            required=True,
            location='form',
            schema=coreschema.String(description='Language')
        )
    ]
))
def change_language(request):
    response = {'success': False}
    data = request.data
    user = request.user
    user_profile = user.profiles.first()
    user_profile.language = Language.objects.get(code=data['language'])
    user_profile.save()
    response['success'] = True
    return Response(response)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'action',
            required=True,
            location='form',
            schema=coreschema.String(description='Action')
        ),
        coreapi.Field(
            'email',
            required=False,
            location='form',
            schema=coreschema.String(description='Email')
        ),
        coreapi.Field(
            'code',
            required=False,
            location='form',
            schema=coreschema.String(description='Code')
        )
    ]
))
def reset_password(request):
    response = {'success': False}
    data = request.data
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
    return Response(response)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'verificationCode',
            required=True,
            location='form',
            schema=coreschema.String(description='Verification code')
        )
    ]
))
def get_signature_code(request):
    response = {}
    data = request.data
    vcode = data['verificationCode']
    forum_profile = ForumProfile.objects.get(verification_code=vcode)
    if config.TEST_MODE:
        sig_code = forum_profile.signature.test_signature
    else:
        sig_code = forum_profile.signature.code
    response['signature_code'] = inject_verification_code(sig_code, vcode)
    response['success'] = True
    return Response(response)


@api_view(['GET'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'email',
            required=True,
            location='form',
            schema=coreschema.String(description='Email')
        )
    ]
))
def check_email_exists(request):
    data = request.data
    response = {'success': True, 'email_exists': True}
    user_check = User.objects.filter(email=data['email'].lower())
    if not user_check.exists():
        response['email_exists'] = False
    return Response(response)


@api_view(['GET'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'username',
            required=True,
            location='form',
            schema=coreschema.String(description='Username')
        )
    ]
))
def check_username_exists(request):
    data = request.data
    response = {'success': True, 'username_exists': True}
    user_check = User.objects.filter(username=data['username'].lower())
    if not user_check.exists():
        response['username_exists'] = False
    return Response(response)


@api_view(['GET'])
def get_languages(request):
    languages = Language.objects.filter(active=True)
    languages = [{'value': x.code, 'text': x.name} for x in languages]
    return Response(languages)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def generate_2fa_uri(request):
    response = {}
    user = request.user
    profile = user.profiles.first()
    email = user.email
    if profile.otp_secret:
        otp_secret = decrypt_data(profile.otp_secret, settings.SECRET_KEY)
    else:
        otp_secret = pyotp.random_base32()
        profile.otp_secret = encrypt_data(otp_secret, settings.SECRET_KEY)
        profile.save()
    totp = pyotp.totp.TOTP(otp_secret)
    uri = totp.provisioning_uri(email, issuer_name='Volentix Venue')
    response['success'] = True
    response['uri'] = uri
    return Response(response)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'otpCode',
            required=True,
            location='form',
            schema=coreschema.String(description='OTP code')
        ),
        coreapi.Field(
            'enable_2fa',
            required=False,
            location='form',
            schema=coreschema.String(description='OTP code')
        )
    ]
))
def verify_2fa_code(request):
    response = {}
    data = request.data
    profile = request.user.profiles.first()
    otp_secret = decrypt_data(profile.otp_secret, settings.SECRET_KEY)
    totp = pyotp.totp.TOTP(otp_secret)
    verified = totp.verify(data['otpCode'])
    if verified:
        if 'enable_2fa' in data.keys() and data['enable_2fa']:
            profile.enabled_2fa = True
            profile.save()
    response['verified'] = verified
    response['success'] = True
    return Response(response)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def disable_2fa(request):
    response = {}
    profile = request.user.profiles.first()
    profile.enabled_2fa = False
    profile.save()
    response['success'] = True
    return Response(response)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_notifications(request):
    response = {}
    profile = request.user.profiles.first()
    notifs = Notification.objects.filter(active=True).exclude(
        dismissed_by=request.token.user
    )
    if profile.enabled_2fa:
        notifs = notifs.exclude(code='2fA_notification')
    response['notifications'] = notifs.values()
    response['success'] = True
    return Response(response)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'notificationId',
            required=True,
            location='form',
            schema=coreschema.String(description='Notification ID')
        )
    ]
))
def dismiss_notification(request):
    response = {}
    data = request.data
    notif = Notification.objects.get(id=data['notificationId'])
    notif.dismissed_by.add(request.user)
    response['success'] = True
    return Response(response)


class ForumSiteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=50)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_forum_sites(request):
    response = {'status': False}
    sites = ForumSite.objects.all()
    if sites.count():
        serializer = ForumSiteSerializer(sites, many=True)
        response['forum_sites'] = serializer.data
    return Response(response)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'profile_url',
            required=True,
            location='form',
            schema=coreschema.String(description='Profile URL')
        ),
        coreapi.Field(
            'forum_id',
            required=False,
            location='form',
            schema=coreschema.String(description='Forum ID')
        )
    ]
))
def creat_forum_profile(request):
    data = request.data
    user_profile = UserProfile.objects.get(user=request.user)
    return Response({'success': True})
    """
    # TODO - finish this!
    forum = ForumSite.objects.get(id=forum_id)
    info = get_user_position(forum_id, profile_url, self.request.user.id)
    profile_check = ForumProfile.objects.filter(
        forum_user_id=info['forum_user_id'],
        forum=forum
    )
    if profile_check.exists():
        fps = profile_check.filter(active=True, verified=True)
        fp = fps.last()
        if fp and fp.signature:
            error_message = 'Your profile already contains our signature.'
            raise serializers.ValidationError(error_message)
    else:
        rank, created = ForumUserRank.objects.get_or_create(
            name=info['position'],
            forum_site=forum
        )
        del created
        serializer.save(
            user_profile=user_profile,
            forum_user_id=info['forum_user_id'],
            forum=forum,
            forum_rank=rank,
            active=True
        )
    """


class ForumProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    forum_user_id = serializers.IntegerField()


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_id',
            required=True,
            location='form',
            schema=coreschema.String(description='Forum site ID')
        ),
        coreapi.Field(
            'forum_user_id',
            required=True,
            location='form',
            schema=coreschema.String(description='Forum user ID')
        )
    ]
))
def get_forum_profiles(request):
    data = request.query_params
    response = {'success': False}
    forum_profiles = ForumProfile.objects.filter(
        forum_id=data.get('forum_id'),
        forum_user_id=data.get('forum_user_id')
    )
    if forum_profiles.count():
        response['success'] = True
        serializer = ForumProfileSerializer(forum_profiles, many=True)
        response['forum_profiles'] = serializer.data
    return Response(response)


def inject_verification_code(sig_code, verification_code):

    def repl(m):
        return '%s?vcode=%s' % (m.group(), verification_code)

    if 'http' in sig_code:
        pattern = r'http[s]?://([a-z./-?=&])+'
        return re.sub(pattern, repl, sig_code)
    elif 'link' in sig_code:
        return sig_code + '?vcode=' + verification_code
    else:
        return sig_code


class SignatureSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    image = serializers.CharField(max_length=200)
    code = serializers.CharField(max_length=200)
    usage_count = serializers.IntegerField()


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_site_id',
            required=True,
            location='form',
            schema=coreschema.String(description='Forum site ID')
        ),
        coreapi.Field(
            'forum_user_rank',
            required=True,
            location='form',
            schema=coreschema.String(description='Forum user rank')
        ),
        coreapi.Field(
            'forum_profile_id',
            required=True,
            location='form',
            schema=coreschema.String(description='Forum profile ID')
        )
    ]
))
def get_signatures(request):
    data = request.query_params
    response = {'success': False}
    signatures = Signature.objects.filter(
        forum_site_id=data.get('forum_site_id'),
        user_ranks__name=data.get('forum_user_rank')
    )
    if signatures.count():
        forum_profile = ForumProfile.objects.get(id=data.get('forum_profile_id'))
        for sig in signatures:
            if config.TEST_MODE:
                sig_code = sig.test_signature
            else:
                sig_code = sig.code
            sig.code = inject_verification_code(
                sig_code,
                forum_profile.verification_code
            )
            sig.usage_count = sig.users.count()
        response['success'] = True
        serializer = SignatureSerializer(signatures, many=True)
        response['signatures'] = serializer.data
    return Response(response)
