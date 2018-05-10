"""
Volentix VENUE
View functions
"""

from operator import itemgetter
from datetime import timedelta
import re
import pyotp
import coreschema
import coreapi
from hashids import Hashids
from constance import config
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.conf import settings
from venue.utils import encrypt_data, decrypt_data
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.decorators import api_view, schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.schemas import AutoSchema
from .tasks import (verify_profile_signature, get_user_position, update_data,
                    send_email_confirmation, send_deletion_confirmation,
                    send_email_change_confirmation, send_reset_password)
from .models import (UserProfile, ForumSite, ForumProfile, Notification,
                     Language, Signature, ForumUserRank)

from .utils import RedisTemp


# Instantiate a Hashids instance to be used later
hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)


# Function that converts points to percentages
def points_to_percentage(points, category=None):
    """ Converts points to percentages 
    # categories = posts / uptime / influence / total
    """
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
    """ Authenticates a user """
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
    """ Retrieves user details """
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
    """ Creates new user """
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


# ----------------------
# Confirm email endpoint
# ----------------------


CONFIRM_EMAIL_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'code',
            required=True,
            location='query',
            schema=coreschema.String(description='Confirmation code')
        )
    ]
)


@api_view(['GET'])
@schema(CONFIRM_EMAIL_SCHEMA)
def confirm_email(request):
    """ Confirms email address """
    code = request.query_params.get('code')
    user_id, = hashids.decode(code)
    user_profile = UserProfile.objects.get(user_id=user_id)
    user_profile.email_confirmed = True
    user_profile.save()
    return redirect('%s/#/?email_confirmed=1' % settings.VENUE_FRONTEND)


# ----------------------
# Check profile endpoint
# ----------------------


CHECK_PROFILE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_profile_id',
            required=True,
            location='query',
            schema=coreschema.String(description='Forum profile ID')
        ),
        coreapi.Field(
            'signature_id',
            required=True,
            location='query',
            schema=coreschema.String(description='Signature ID')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(CHECK_PROFILE_SCHEMA)
def check_profile(request):
    """ Checks forum profile existence """
    data = request.query_params
    user = request.user
    forum = ForumSite.objects.get(id=data.get('forum'))
    response = {'found': False, 'forum_id': data.get('forum')}
    info = get_user_position(forum.id, data.get('profile_url'), user.id)
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


# -----------------------
# Save signature endpoint
# -----------------------


SAVE_SIGNATURE_SCHEMA = AutoSchema(
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
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(SAVE_SIGNATURE_SCHEMA)
def save_signature(request):
    """ Saves signature """
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


# -------------------------
# Get site configs endpoint
# -------------------------


@api_view(['GET'])
def get_site_configs(request):
    """ Retrieves some global site configs """
    configs = {
        'disable_sign_up': config.DISABLE_SIGN_UP
    }
    return Response(configs)


# ------------------
# Get stats endpoint
# ------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_stats(request):
    """ Retrieves the stats of the user """
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
        for fp in fps:
            fp_data = {
                'User_ID': fp.forum_user_id,
                'forumSite': fp.forum.name,
                'forumUserId': fp.forum_user_id,
                'forumUserRank': fp.forum_rank.name,
                'numPosts': fp.total_posts,
                'postPoints': fp.post_points,
                'uptimeSeconds': fp.uptime_seconds,
                'uptimePoints': fp.uptime_points,
                'totalPoints': fp.total_points
            }
            profile_stats.append(fp_data)
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
            data['posts'] = user_profile.get_num_posts(date=day)
            data['rank'] = user_profile.get_ranking(date=day)
            data['date'] = day
            userlevel_stats['daily_stats'].append(data)
        # Points, tokens, and overall user rank
        userlevel_stats['num_posts'] = user_profile.get_num_posts()
        userlevel_stats['post_points'] = 0
        userlevel_stats['uptime_points'] = 0
        userlevel_stats['total_points'] = 0
        userlevel_stats['total_tokens'] = 0
        userlevel_stats['overall_rank'] = user_profile.get_ranking()
        stats['user_level'] = userlevel_stats
        # -------------------------
        # Generate site-wide stats
        # -------------------------
        sitewide_stats = {}
        users = UserProfile.objects.filter(email_confirmed=True)
        users_with_fp = [x.id for x in users if x.with_forum_profile]
        total_posts = [x.get_num_posts() for x in users]
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


# -----------------------------
# Get leaderboard data endpoint
# -----------------------------


@api_view(['GET'])
def get_leaderboard_data(request):
    """ Retrieves leaderboard stats data """
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


# -----------------------
# Delete account endpoint
# -----------------------


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def delete_account(request):
    """ Deletes account """
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
            return redirect('%s/#/?account_deleted=1' % settings.VENUE_FRONTEND)
        else:
            return Response({'success': False})


# ---------------------
# Change email endpoint
# ---------------------


CHANGE_EMAIL_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'email',
            required=False,
            location='form',
            schema=coreschema.String(description='New email')
        ),
        coreapi.Field(
            'code',
            required=False,
            location='query',
            schema=coreschema.String(description='Confirmation code')
        )
    ]
)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
@schema(CHANGE_EMAIL_SCHEMA)
def change_email(request):
    """ Changes user's email """
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
        return redirect('%s/#/settings/?updated_email=1' % settings.VENUE_FRONTEND)


# ------------------------
# Change username endpoint
# ------------------------


CHANGE_USERNAME_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'username',
            required=True,
            location='form',
            schema=coreschema.String(description='Username')
        )
    ]
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(CHANGE_USERNAME_SCHEMA)
def change_username(request):
    """ Changes user's username """
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


# ------------------------
# Change password endpoint
# ------------------------


CHANGE_PASSWORD_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'password',
            required=True,
            location='form',
            schema=coreschema.String(description='Password')
        )
    ]
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(CHANGE_PASSWORD_SCHEMA)
def change_password(request):
    """ Changes user's password """
    data = request.data
    response = {}
    user = User.objects.get(id=request.user.id)
    user.set_password(data['password'])
    user.save()
    response['success'] = True
    return Response(response)


# ------------------------
# Change language endpoint
# ------------------------


CHANGE_LANGUAGE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'language',
            required=True,
            location='form',
            schema=coreschema.String(description='Language')
        )
    ]
)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@schema(CHANGE_LANGUAGE_SCHEMA)
def change_language(request):
    """ Changes language preference """
    response = {'success': False}
    data = request.data
    user = request.user
    user_profile = user.profiles.first()
    user_profile.language = Language.objects.get(code=data['language'])
    user_profile.save()
    response['success'] = True
    return Response(response)


# -----------------------
# Reset password endpoint
# -----------------------


RESET_PASSWORD_SCHEMA = AutoSchema(
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
)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@schema(RESET_PASSWORD_SCHEMA)
def reset_password(request):
    """ Resets user's password """
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


# ---------------------------
# Get signature code endpoint
# ---------------------------


GET_SIGCODE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'verificationCode',
            required=True,
            location='form',
            schema=coreschema.String(description='Verification code')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(GET_SIGCODE_SCHEMA)
def get_signature_code(request):
    """ Retrieves signature code """
    response = {'success': False}
    data = request.query_params
    if data.get('verificationCode'):
        vcode = data.get('verificationCode')
        forum_profile = ForumProfile.objects.get(verification_code=vcode)
        if config.TEST_MODE:
            sig_code = forum_profile.signature.test_signature
        else:
            sig_code = forum_profile.signature.code
        response['signature_code'] = inject_verification_code(sig_code, vcode)
        response['success'] = True
    return Response(response)


# --------------------
# Check email endpoint
# --------------------


CHECK_EMAIL_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'email',
            required=True,
            location='query',
            schema=coreschema.String(description='Email')
        )
    ]
)


@api_view(['GET'])
@schema(CHECK_EMAIL_SCHEMA)
def check_email_exists(request):
    """ Checks if email exists """
    data = request.query_params
    response = {'success': True, 'email_exists': False}
    if data.get('email'):
        user_check = User.objects.filter(email=data.get('email').lower())
        if user_check.exists():
            response['email_exists'] = True
    return Response(response)


# -----------------------
# Check username endpoint
# -----------------------


CHECK_USERNAME_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'username',
            required=True,
            location='query',
            schema=coreschema.String(description='Username')
        )
    ]
)


@api_view(['GET'])
@schema(CHECK_USERNAME_SCHEMA)
def check_username_exists(request):
    """ Checks if username exists """
    data = request.query_params
    response = {'success': True, 'username_exists': False}
    if data.get('username'):
        user_check = User.objects.filter(username=data.get('username').lower())
        if user_check.exists():
            response['username_exists'] = True
    return Response(response)


# ----------------------
# Get langauges endpoint
# ----------------------


@api_view(['GET'])
def get_languages(request):
    """ Retrieves available languages """
    languages = Language.objects.filter(active=True)
    languages = [{'value': x.code, 'text': x.name} for x in languages]
    return Response(languages)


# -------------------------
# Generate 2FA URI endpoint
# -------------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def generate_2fa_uri(request):
    """ Generates two-factor authentication URI """
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
    response['service'] = 'Volentix Venue'
    response['account'] = email
    response['key'] = otp_secret
    response['uri'] = uri
    return Response(response)


# ------------------------
# Verify 2FA code endpoint
# ------------------------


VERIFY_2FA_SCHEMA = AutoSchema(
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
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(VERIFY_2FA_SCHEMA)
def verify_2fa_code(request):
    """ Verifies two-factor auth OTP code """
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


# --------------------
# Disable 2FA endpoint
# --------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def disable_2fa(request):
    """ Disables two-factor authentication """
    response = {}
    profile = request.user.profiles.first()
    profile.enabled_2fa = False
    profile.otp_secret = ''
    profile.save()
    response['success'] = True
    return Response(response)


# --------------------------
# Get notifications endpoint
# --------------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_notifications(request):
    """ Retrieves notifications """
    response = {}
    profile = request.user.profiles.first()
    notifs = Notification.objects.filter(active=True).exclude(
        dismissed_by=request.user
    )
    if profile.enabled_2fa:
        notifs = notifs.exclude(code='2fA_notification')
    response['notifications'] = notifs.values()
    response['success'] = True
    return Response(response)


# -----------------------------
# Dismiss notification endpoint
# -----------------------------


DISMISS_NOTIFICATION_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'notificationId',
            required=True,
            location='form',
            schema=coreschema.String(description='Notification ID')
        )
    ]
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(DISMISS_NOTIFICATION_SCHEMA)
def dismiss_notification(request):
    """ Dismisses a notification """
    response = {}
    data = request.data
    notif = Notification.objects.get(id=data['notificationId'])
    notif.dismissed_by.add(request.user)
    response['success'] = True
    return Response(response)


# ------------------------
# Get forum sites endpoint
# ------------------------


class ForumSiteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=50)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_forum_sites(request):
    """ Retrieves list of forum sites """
    response = {'status': False}
    sites = ForumSite.objects.all()
    if sites.count():
        serializer = ForumSiteSerializer(sites, many=True)
        response['forum_sites'] = serializer.data
    return Response(response)


# -----------------------------
# Create forum profile endpoint
# -----------------------------


CREATE_FORUM_PROFILE_SCHEMA = AutoSchema(
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
)


class SignatureAlreadyExists(APIException):
    status_code = 503
    default_detail = 'Your profile already contains our signature.'
    default_code = 'signature_already_exists'


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(CREATE_FORUM_PROFILE_SCHEMA)
def create_forum_profile(request):
    """ Creates a forum profile """
    data = request.data
    response = {'success': False}
    forum = ForumSite.objects.get(id=data['forum_id'])
    info = get_user_position(
        data['forum_id'],
        data['profile_url'],
        request.user.id
    )
    profile_check = ForumProfile.objects.filter(
        forum_user_id=info['forum_user_id'],
        forum=forum
    )
    if profile_check.exists():
        fps = profile_check.filter(active=True, verified=True)
        fp = fps.last()
        if fp and fp.signature:
            raise SignatureAlreadyExists()
    else:
        rank, created = ForumUserRank.objects.get_or_create(
            name=info['position'],
            forum_site=forum
        )
        del created
        user_profile = UserProfile.objects.get(user=request.user)
        fp_object = ForumProfile(
            user_profile=user_profile,
            forum_user_id=info['forum_user_id'],
            forum_username=info['forum_user_name'],
            forum=forum,
            forum_rank=rank,
            active=True
        )
        fp_object.save()
        response['id'] = fp_object.id
        response['success'] = True
    return Response(response)


# ---------------------------
# Get forum profiles endpoint
# ---------------------------


class ForumProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    forum_user_id = serializers.IntegerField()


GET_FORUM_PROFILES_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_id',
            required=True,
            location='query',
            schema=coreschema.String(description='Forum site ID')
        ),
        coreapi.Field(
            'forum_user_id',
            required=True,
            location='query',
            schema=coreschema.String(description='Forum user ID')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(GET_FORUM_PROFILES_SCHEMA)
def get_forum_profiles(request):
    """ Retrieves forum profiles """
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


# -----------------------
# Get signatures endpoint
# -----------------------


def inject_verification_code(sig_code, verification_code):
    """ Helper function for injecting verification code to signature """
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
    verification_code = serializers.CharField(max_length=200)
    usage_count = serializers.IntegerField()
    forum_site_name = serializers.CharField(max_length=30, required=False)
    forum_user_name = serializers.CharField(max_length=30, required=False)
    forum_userid = serializers.CharField(max_length=20, required=False)


GET_SIGNATURES_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_site_id',
            required=False,
            location='form',
            schema=coreschema.String(description='Forum site ID')
        ),
        coreapi.Field(
            'forum_user_rank',
            required=False,
            location='form',
            schema=coreschema.String(description='Forum user rank')
        ),
        coreapi.Field(
            'forum_profile_id',
            required=False,
            location='query',
            schema=coreschema.String(description='Forum profile ID')
        ),
        coreapi.Field(
            'own_sigs',
            required=False,
            location='query',
            schema=coreschema.String(description='Get own signatures')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(GET_SIGNATURES_SCHEMA)
def get_signatures(request):
    """ Retrives list of signatures """
    data = request.query_params
    response = {'success': False}
    if data.get('own_sigs') == '1':
        forum_profiles = ForumProfile.objects.filter(
            user_profile__user=request.user,
            verified=True
        )
        signatures = Signature.objects.filter(
            id__in=forum_profiles.values_list('signature_id', flat=True)
        )
        fp_map = {x.signature.id: x.id for x in forum_profiles}
    else:
        signatures = Signature.objects.filter(
            forum_site_id=data.get('forum_site_id'),
            user_ranks__name=data.get('forum_user_rank')
        )
    if signatures.count():
        for sig in signatures:
            if config.TEST_MODE:
                sig_code = sig.test_signature
            else:
                sig_code = sig.code
            if data.get('forum_profile_id'):
                forum_profile = ForumProfile.objects.get(
                    id=data.get('forum_profile_id')
                )
            else:
                forum_profile = ForumProfile.objects.get(
                    id=fp_map[sig.id]
                )
            verification_code = forum_profile.verification_code
            sig.code = inject_verification_code(
                sig_code,
                verification_code
            )
            sig.usage_count = sig.users.count()
            sig.verification_code = verification_code
            sig.forum_site_name = forum_profile.forum.name
            sig.forum_user_name = forum_profile.forum_username
            sig.forum_userid = forum_profile.forum_user_id
        response['success'] = True
    serializer = SignatureSerializer(signatures, many=True)
    response['signatures'] = serializer.data
    return Response(response)
