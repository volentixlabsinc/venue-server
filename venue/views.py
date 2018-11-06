"""
Volentix VENUE
View functions 
"""

import re
from datetime import timedelta
from operator import itemgetter

import coreapi
import coreschema
import pyotp
import shortuuid
import rollbar

from celery.result import AsyncResult
from constance import config
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from knox.models import AuthToken
from knox.settings import CONSTANTS as KNOX_CONSTANTS
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from django.db import IntegrityError

from .models import (ForumPost, ForumProfile, ForumSite, ForumUserRank, Notification, Signature, UserProfile,
                     compute_total_points, Referral)
from .tasks import (get_user_position, send_deletion_confirmation, send_email_change_confirmation,
                    send_email_confirmation, send_reset_password, set_scraping_rate, update_data,
                    verify_profile_signature, send_email)
from .utils import RedisTemp, decrypt_data, encrypt_data, check_language_exists, translation_on


def generate_token_salt(user):
    token = AuthToken.objects.create(user=user)
    token_key = token[:KNOX_CONSTANTS.TOKEN_KEY_LENGTH]
    token_obj = AuthToken.objects.get(token_key=token_key)
    return token_obj.salt


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
    print('Home page loaded')
    return HttpResponse('Volentix Venue API Server')


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
    """ Authenticates a user

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "token": <string>,
                "username": <string>,
                "email": <string>,
                "user_profile_id": <string>,
                "email_confirmed": <boolean>,
                "language": <string>
            }

        * `success` - Whether authentication was successful or not
        * `token` - Authentication token string
        * `username` - User's username
        * `email` - User's email
        * `user_profile_id` - Profile ID of the user in the DB
        * `email_confirmed` - Whether user's email is confirmed or not
        * `language` - User's selected language code or system's default

    * Status code 400

            {
                "success": <boolean: false>,
                "error_code": <string>
            }

        * `error_code` - Code of the error
    """
    data = request.data
    response = {'success': False}
    error_code = 'unknown_error'
    resp_status = status.HTTP_400_BAD_REQUEST
    try:
        if '@' in data['username']:
            user = User.objects.get(
                email__iexact=data['username']
            )
        else:
            user = User.objects.get(
                username__iexact=data['username']
            )
        pass_check = user.check_password(data['password'])
        if pass_check:
            if user.is_active:
                profile = user.profiles.first()
                proceed = False
                if profile.email_confirmed:
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
                else:
                    error_code = 'email_verification_required'
                    resp_status = status.HTTP_403_FORBIDDEN
                if proceed:
                    token = AuthToken.objects.create(user=user)
                    user.last_login = timezone.now()
                    user.save()
                    user_profile = user.profiles.first()
                    response = {
                        'success': True,
                        'token': token,
                        'username': user.username,
                        'email': user.email,
                        'user_profile_id': user_profile.id,
                        'email_confirmed': user_profile.email_confirmed,
                        'language': user_profile.language
                    }
                    resp_status = status.HTTP_200_OK
            else:
                error_code = 'user_deactivated'
                resp_status = status.HTTP_403_FORBIDDEN
        else:
            error_code = 'wrong_credentials'
    except User.DoesNotExist:
        error_code = 'wrong_credentials'
    if not response['success']:
        response['error_code'] = error_code
    return Response(response, status=resp_status)


# ---------------
# Logout endpoint
# ---------------


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def logout_user(request):
    """ Logs out a user

    ### Response

    * Status code 200

            {'success': <boolean: true>}

        * `success` - Whether the user has been logged out or not

    * Status code 401 (When logout fails)
    """
    request._auth.delete()
    return Response({'success': True})


# -------------------------
# Get user details endpoint
# -------------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_user(request):
    """ Retrieves user details

    ### Response

    * Status code 200

            {
                'found': <boolean>,
                'username': <string>,
                'email': <string>,
                'language': <string>,
                'email_confirmed': <boolean>,
                'enabled_2fa': <boolean>
                'referral_code': <string>
            }

        * `found` - Whether a user and user profile are found or not
        * `username` - User's username
        * `email` - User's email
        * `language` - Code of the user's selected language
        * `email_confirmed` - Whether the user's email is confirmed or not
        * `enabled_2fa` - Whether the user has enabled 2FA or not
        * `referral_code` - User's referral_code
    """
    data = {'found': False}
    user_profile = request.user.profiles.first()
    if user_profile:
        data = {
            'found': True,
            'username': request.user.username,
            'email': request.user.email,
            'language': user_profile.language,
            'email_confirmed': user_profile.email_confirmed,
            'enabled_2fa': user_profile.enabled_2fa,
            'referral_code': user_profile.referral_code
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
            'receive_emails',
            required=False,
            location='form',
            schema=coreschema.Boolean(description='Receive newsletter emails'),
            description='Boolean field to receive emails'
        ),
        coreapi.Field(
            'language',
            required=False,
            location='form',
            schema=coreschema.String(description='Language code')
        ),
        coreapi.Field(
            'referral_code',
            required=False,
            location='form',
            schema=coreschema.String(description='Referral code')
        )
    ]
)


@api_view(['POST'])
@schema(CREATE_USER_SCHEMA)
def create_user(request):
    """ Creates new user

    ### Response

    * Status code 201

            {
                "success": <boolean: true>,
                "user": {
                    "username": <string>,
                    "email": <string>
                }
            }

        * `success` - Whether creation of user succeeded or not
        * `user` - An array containing user details
        * `username` - User's username
        * `email` - User's email

    * Status code 422 (When the create request cannot be processed)

            {
                "success": <boolean: false>,
                "message": <string>
            }

        * `message` - Error message. Possible values:
            - not_whitelisted
            - username_too_long
            - user_already_exists
            - wrong_language

    * Status code 403 (When the user is not allowed to register)
    """
    data = request.data
    data['email'] = data['email'].lower()
    # Check if a user with confirmed email same as the given already exists
    user_check = UserProfile.objects.filter(
        user__email__iexact=data['email'].strip(),
        email_confirmed=True
    )
    response = {'success': False}
    proceed = True
    # get referrer profile
    referral_code = data.pop('referral_code', None)
    referrer_user_profile = UserProfile.get_by_referral_code(referral_code)
    if config.CLOSED_BETA_MODE:
        if not data['email'] in config.SIGN_UP_WHITELIST.splitlines():
            proceed = False
            response['message'] = 'not_whitelisted'
            resp_status = status.HTTP_403_FORBIDDEN
    if data.get('username'):
        if len(data['username']) > 25:
            proceed = False
            response['message'] = 'username_too_long'
            resp_status = status.HTTP_422_UNPROCESSABLE_ENTITY

    language = data.pop('language', None)
    language = settings.LANGUAGE_CODE if language is None else language
    if not check_language_exists(language):
        proceed = False
        response['message'] = 'wrong_language'
        resp_status = status.HTTP_422_UNPROCESSABLE_ENTITY

    if proceed:
        try:
            receive_emails = data.pop('receive_emails', False)
            if user_check:
                response['message'] = 'user_already_exists'
                resp_status = status.HTTP_422_UNPROCESSABLE_ENTITY
            # referral_code exists but wrong
            elif referral_code is not None and referrer_user_profile is None:
                response['message'] = 'wrong_referral_code'
                resp_status = status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                user = User.objects.create_user(**data)
                user_data = {
                    'username': user.username,
                    'email': user.email
                }
                response['user'] = user_data
                user_profile, _ = UserProfile.objects.get_or_create(
                    user=user
                )
                user_profile.receive_emails = receive_emails
                user_profile.language = language
                user_profile.save()

                if referral_code and referrer_user_profile:
                    Referral.objects.create(
                        referral=user_profile,
                        referrer=referrer_user_profile
                    )

                # Send confirmation email
                token_salt = generate_token_salt(user)
                send_email_confirmation.delay(user.email, user.username, token_salt, language)
                response['success'] = True
                resp_status = status.HTTP_200_OK
        except Exception as exc:
            response['message'] = str(exc)
            resp_status = status.HTTP_400_BAD_REQUEST
    return Response(response, status=resp_status)


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
    """ Confirms email address

    ### Response

    * Status code 301 (When email is confirmed)

        Redirects to `<domain>/#/?email_confirmed=1`

    * Status code 400
            {
                "success": <boolean: false>,
                "message": <string: "not_found">
            }
    
        * `message` - Error message

    """
    code = request.query_params.get('code')
    try:
        token = AuthToken.objects.get(salt=code)
        user_profile = UserProfile.objects.get(user=token.user)
        user_profile.email_confirmed = True
        user_profile.save()
    except AuthToken.DoesNotExist:
        return Response(
            {'success': False, 'message': 'not_found'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return redirect('%s/login?email_confirmed=1' % settings.VENUE_FRONTEND)


# ----------------------
# Check profile endpoint
# ----------------------


CHECK_PROFILE_SCHEMA = AutoSchema(
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
            schema=coreschema.String(
                description='Profile URL or forum user ID'
            )
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(CHECK_PROFILE_SCHEMA)
def check_profile(request):
    """ Checks forum profile existence

    ### Response

    * Status code 200 (when profile is found)

            {
                "found": <boolean: true>,
                "forum_id": <string>,
                "position": <string>,
                "position_allowed": <boolean>,
                "forum_user_id": <string>,
                "exists": <boolean>,
                "status_code": <int>
            }

        * `found` - Whether the forum user ID is found in the forum site or not
        * `forum_id` - ID of the forum in the DB
        * `position` - Forum position or rank of the user
        * `position_allowed` - Whether the position is allowed to participate or not
        * `forum_user_id` - User's user ID in the forum
        * `exists` - Whether the profile exists in DB or not
        * `status_code` - Status code of the forum profile scraping request

    * Status code 400 (when profile is not found)

            {
                "found": <boolean: false>,
                "forum_id": <int>,
                "status_code": <int>,
                "message": <string>,
                "num_retries": <int>,
                "fallback": <string>
            }

        * `message` - Error message: `scraping_error` or `profile_does_not_exist`
        * `num_retries` - Number of retries before giving up
        * `fallback` - Fallback scraping method used
    """
    data = request.query_params
    user = request.user
    forum_id = data.get('forum_id')
    if str(forum_id) == '1':
        forum_site = ForumSite.objects.get(name='bitcointalk.org')
        forum_id = str(forum_site.id)
    forum = ForumSite.objects.get(id=forum_id)
    response = {
        'forum_id': data.get('forum_id')
    }
    task = get_user_position.delay(
        forum.id,
        data.get('forum_user_id'),
        user.id
    )
    task.get(timeout=10)
    info = task.result
    response['found'] = info['found']
    if info['found']:
        if info['status_code'] == 200 and info['position']:
            resp_status = status.HTTP_200_OK
            response['position'] = info['position']
            allowed = False
            try:
                forum_rank = ForumUserRank.objects.get(
                    forum_site=forum,
                    name__iexact=info['position'].strip()
                )
                if forum_rank.allowed or config.TEST_MODE:
                    allowed = True
            except ForumUserRank.DoesNotExist as exc:
                rollbar.report_message(
                    f'{exc}, username: {user}, user_id: {user.id}, info: {info}',
                    'warning'
                )
            response['position_allowed'] = allowed
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
    else:
        resp_status = status.HTTP_400_BAD_REQUEST
        response.update(info)
    return Response(response, status=resp_status)


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
    log_opts = {
        'level': 'info',
        'meta': {}
    }

    """ Saves signature

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "task_id": <string>
            }

        * `success` - Whether saving the signature succeeded or not
        * `task_id` - ID of background task that scraped the profile

    * Status code 400

            {
                "success": <boolean: false>,
                "message": <string>
            }

        * `message` - Error message
    """
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
        resp_status = status.HTTP_200_OK
    else:
        response['success'] = False
        response['message'] = 'signature_not_found'
        resp_status = status.HTTP_400_BAD_REQUEST
    return Response(response, status=resp_status)


# -------------------------
# Get site configs endpoint
# -------------------------


@api_view(['GET'])
def get_site_configs(request):
    """ Retrieves some global site configs

    ### Response

    * Status code 200

            {
                "disable_sign_up": <boolean>
            }

        * `disable_sign_up` - Whether the sign up is disabled or not

    """
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
    """ Retrieves the stats of the user

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "stats": {
                    "fresh": <boolean>,
                    "sitewide": {
                        "total_users": <int>,
                        "total_posts": <int>,
                        "available_tokens": <int>
                    }
                    "user_level": {
                        "daily_stats": <list: DailyStats>,
                        "total_posts": <int>,
                        "total_points": <int>,
                        "total_points_pct": <int>,
                        "total_tokens": <int>,
                        "overall_rank": <int>
                    },
                    "profile_level": <list: ProfileStats>
                }
            }

        * `success` - Whether the request succeeded or not
        * `stats` - Stats array
        * `fresh` - Whether this account is fresh (no stats) or not
        * `sitewide` - Sitewide stats array
        * `total_users` - Total users sitewide
        * `total_posts` - Total posts sitewide
        * `available_tokens` - Available tokens sitewide
        * `user_level` - User-level stats array
        * `daily_stats` - Post and rank stats for the last seven days
        * `total_posts` - Total number of posts
        * `total_points` - Total points earned
        * `total_points_pct` - Percentage of points compared to all users
        * `total_tokens` - Total tokens earned by the user
        * `profile_level` - Profile level stats array

        <br>Each `ProfileStats` array contains the following info

            {
                "User_ID": <string>,
                "forumSite": <string>,
                "forumUserId": <string>,
                "forumUserRank": <string>,
                "rankBonusPercentage": <int>,
                "numPosts": <int>,
                "totalPoints": <int>,
                "VTX_Tokens": <int>
            }

        * `forumSite` - Name of the forum site
        * `forumUserId` - User's forum user ID
        * `forumUserRank` - User's forum rank/position
        * `numPosts` - User's total forum posts
        * `totalPoints` - User's total points earned
        * `VTX_Tokens` - User's total VTX tokens earned

        <br>Each `DailyStats` array contains the following info

            {
                "posts": {
                    "credited": <int>,
                    "pending": <int>,
                    "total": <int>
                },
                "rank": <int> or <null>,
                "date": <string>
            }

        * `posts` - Post stats array
        * `credited` - Posts that have been credited with points
        * `pending` - Posts that are not yet credited with points
        * `total` - Total number of posts
        * `rank` - User's rank
        * `date` - Date string
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
    global_total_pts = compute_total_points()
    if fps.count():
        for fp in fps:
            fp_data = {
                'forumSite': fp.forum.name,
                'forumUserId': fp.forum_user_id,
                'forumUserRank': fp.forum_rank.name,
                'rankBonusPercentage': fp.forum_rank.bonus_percentage,
                'numPosts': fp.total_posts,
                'totalPoints': fp.total_points,
                'VTX_Tokens': 0
            }
            if global_total_pts:
                pct_contrib = float(fp.total_points) / global_total_pts
                fp_tokens = pct_contrib * config.VTX_AVAILABLE
                fp_data['VTX_Tokens'] = int(round(fp_tokens, 0))
            profile_stats.append(fp_data)
        stats['profile_level'] = profile_stats

        # --------------------------
        # Generate user-level stats
        # --------------------------
        userlevel_stats = {}
        # Get the date string for the last seven days
        now = timezone.now()
        days = (now - timedelta(days=x) for x in range(7))
        days = [str(x.date()) for x in days]
        user_profile = UserProfile.objects.prefetch_related('posts', 'rankings').get(user=request.user)
        userlevel_stats['daily_stats'] = []
        # Iterate over the reversed list
        for day in days[::-1]:
            rank_obj = user_profile.rankings.filter(timestamp__date__lte=day).order_by('-timestamp').first()
            rank = rank_obj.rank if rank_obj is not None else 0
            # posts = user_profile.posts.filter(timestamp__date=day, forum_profile__verified=True).count()
            posts = user_profile.get_num_posts(date=day)
            userlevel_stats['daily_stats'].append(
                {'posts': posts, 'rank': rank, 'date': day}
            )
        # Points, tokens, and overall user rank
        userlevel_stats['total_posts'] = user_profile.get_num_posts()['total']
        total_points = user_profile.total_points
        userlevel_stats['total_points'] = total_points
        if global_total_pts:
            pct_contrib = total_points / global_total_pts
        else:
            pct_contrib = 0
        userlevel_stats['total_points_pct'] = int(round(pct_contrib * 100, 0))
        userlevel_stats['total_tokens'] = user_profile.total_tokens + user_profile.referrals_bonuses
        userlevel_stats['overall_rank'] = user_profile.get_ranking()
        stats['user_level'] = userlevel_stats
        # -------------------------
        # Generate site-wide stats
        # -------------------------
        sitewide_stats = {}
        users_with_fp_count = UserProfile.objects.filter(
            forum_profiles__active=True, forum_profiles__verified=True
        ).count()
        total_posts = ForumPost.objects.filter(forum_profile__verified=True).count()
        sitewide_stats['total_users'] = users_with_fp_count
        sitewide_stats['total_posts'] = total_posts
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
    """ Retrieves leaderboard stats data

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "rankings": <list: Ranking>,
                "sitewide": {
                    "available_tokens": <int>,
                    "total_users": <int>,
                    "total_posts": <int>,
                    "total_points": <int>
                },
                "userstats": {
                    "overall_rank": <int> or <null>,
                    "total_tokens": <int>
                },
                "forumstats": {
                    "posts": <list: ForumPostStat>,
                    "users": <list: ForumUserStats>
                }
            }

        * `success` - Whether the request was successful or not
        * `rankings` - Ordered ranking list
        * `sitewide` - Stats sitewide
        * `available_tokens` - Total available tokens
        * `total_users` - Total number of users
        * `total_posts` - Total number of posts sitewide
        * `total_points` - Total number of points sitewide
        * `userstats` - Stats of the user
        * `overall_rank` - User's overall rank
        * `total_tokens` - Total tokens that the user earned
        * `forumstats` - Stats per forum
        * `posts` - List of forum post stats
        * `users` - List of forum user stats

        <br>Each `Ranking` array contains the following info

            {
                "username": <string>,
                "rank": <int> or <null>,
                "total_posts": <int>,
                "total_points": <int>,
                "total_tokens": <int>
            }

        * `username` - User's username
        * `rank` - User's rank
        * `total_posts` - User's total posts
        * `total_points` - User's total earned points
        * `total_tokens` - User's total earned tokens

        <br>Each `ForumPostStats` array contains the following info

            {
                "forumSite": <string>,
                "value": <int>,
                "color": <string>
            }

        * `forumSite` - Name of the forum site
        * `value` - Number of posts for the forum
        * `color` - Server-generated color for use with graphs

        <br>Each `ForumUserStats` array contains the following info

            {
                "forumSite": <string>,
                "value": <int>,
                "color": <string>
            }

        * `value` - Number of users for the forum
    """
    response = {}
    leader_board_data = UserProfile.get_leader_board_data()
    # Get site-wide stats
    response['sitewide'] = {
        'available_tokens': '{:,}'.format(config.VTX_AVAILABLE),
        'total_users': len(leader_board_data),
        'total_posts': int(sum([x['total_posts'] for x in leader_board_data])),
        'total_points': int(sum([x['total_points'] for x in leader_board_data]))
    }
    # Order according to amount of tokens
    if leader_board_data:
        leader_board_data = sorted(leader_board_data, key=itemgetter('rank'))
        response['rankings'] = leader_board_data
        if request.user.is_anonymous():
            response['userstats'] = {}
        else:
            user_data = next(
                (i for i in leader_board_data if i['username'] == request.user.username),
                {}
            )
            try:
                total_tokens = user_data.get('total_tokens', 0)
                total_tokens = 0 if total_tokens is None else int(total_tokens)
            except ValueError:
                total_tokens = 0
            response['userstats'] = {
                'overall_rank': user_data.get('username'),
                'total_tokens': total_tokens
            }
    # Generate forum stats
    forum_stats = {
        'posts': [],
        'users': []
    }
    sites_stats = ForumSite.get_stats()
    colors = ['#2a96b6', '#5a2998', '#b62da9']
    colors_count = len(colors)
    for i, site_data in enumerate(sites_stats):
        forum_stats['posts'].append({
            'forumSite': site_data['site_name'],
            'value': site_data['total_posts'],
            'color': colors[i % colors_count]
        })
        forum_stats['users'].append({
            'forumSite': site_data['site_name'],
            'value': site_data['total_users'],
            'color': colors[i % colors_count]
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
    """ Deletes account

    ### Response

    **For the `POST` Request**

    This is the deletion request and this does not require any payload

    * Status code 202 (When deletion request is accepted for processing)

            {
                "success": <boolean: true>
            }

        * `success` - Whether the request succeeded or not

    **For the `GET` Request**

    This request occurs when the user clicks on the link in the confirmation email.

    * Status code 301 (When the code is correct)

        Redirects to `<hostname>/#/settings/?account_deleted=1`

    * Status code 400 (When the code is not correct)

            {
                "success": <boolean: false>,
                "message": <string: "wrong_code">
            }

        * `message` - Error message
    """
    response = {'success': False}
    if request.method == 'POST':
        user = request.user
        user_profile = user.profiles.first()

        token_salt = generate_token_salt(user)
        language_code = user_profile.language

        send_deletion_confirmation.delay(
            user.email,
            user.username,
            token_salt,
            language_code
        )
        response['success'] = True
        return Response(response, status=status.HTTP_202_ACCEPTED)
    elif request.method == 'GET':
        code = request.query_params.get('code')
        if code:
            try:
                token = AuthToken.objects.get(salt=code)
                return redirect('%s/#/?account_deleted=1' % settings.VENUE_FRONTEND)
            except AuthToken.DoesNotExist:
                response['message'] = 'wrong_code'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)


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
        )
    ]
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(CHANGE_EMAIL_SCHEMA)
def change_email(request):
    """ Changes user's email

    ### Response

    This request is sent when requesting for email change.
    Refer to the `Request Body` table below for the request payload.

    When the change is processed, an confirmation email is sent to the user.

    * Status code 202 (When email change is accepted for processing)

            {
                "success": <boolean: true>
            }

        * `success` - Whether the request has succeeded or not

    * Status code 302 (When new email submitted already exists)

            {
                "success": <boolean: false>,
                "message": <string: "email_exists">
            }
        
        * `message` - Error message
    """
    rtemp = RedisTemp('new_email')
    data = request.data
    user = request.user
    response = {'success': False}
    email_check = User.objects.filter(email=data['email'].strip())
    if email_check.exists():
        response['message'] = 'email_exists'
        resp_status = status.HTTP_302_FOUND
    else:
        token_salt = generate_token_salt(user)
        rtemp.store(token_salt, data['email'])
        user_profile = user.profiles.first()
        send_email_change_confirmation.delay(
            data['email'],
            user.username,
            token_salt,
            user_profile.language
        )
        response['success'] = True
        resp_status = status.HTTP_202_ACCEPTED
    return Response(response, status=resp_status)


# -----------------------------
# Confirm email change endpoint
# -----------------------------


CONFIRM_EMAIL_CHANGE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'code',
            required=False,
            location='query',
            schema=coreschema.String(description='Confirmation code')
        )
    ]
)


@api_view(['GET'])
@schema(CONFIRM_EMAIL_CHANGE_SCHEMA)
def confirm_email_change(request):
    """ Confirms email change

    ### Response

    This request happens when the user clicks on the link sent in the confirmation email.
    Refer to the `Query Parameters` table below for the request parameters.

    * Status code 301 (When the `code` is correct)

        Redirects to `<hostname>/#/settings/?updated_email=1`

    * Status code 400 (When the `code` is not correct)

            {
                "success": <boolean: false>
            }
    """
    rtemp = RedisTemp('new_email')
    code = request.query_params.get('code')
    response = {'success': False}
    try:
        token = AuthToken.objects.get(salt=code)
        new_email = rtemp.retrieve(code)
        if code and new_email:
            try:
                User.objects.filter(id=token.user.id).update(email=new_email)
                rtemp.remove(code)
                return redirect('%s/#/settings/?updated_email=1' % settings.VENUE_FRONTEND)
            except User.DoesNotExist:
                response['error_code'] = 'user_not_found'
        else:
            response['error_code'] = 'expired_code'
    except AuthToken.DoesNotExist:
        response['error_code'] = 'wrong_code'
    return Response(response, status=status.HTTP_400_BAD_REQUEST)


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
    """ Changes user's username

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "username": <string>,
                "email": <string>
            }

        * `success` - Whether the change request succeeded or not
        * `username` - User's username
        * `email` - User's email

    * Status code 302

            {
                "success": <boolean: false>,
                "message": <string>
            }

        * `message` - Error message
    """
    data = request.data
    user = request.user
    response = {'success': False}
    username_check = User.objects.filter(username__iexact=data['username'].strip())
    if username_check.exists():
        response['message'] = 'username_exists'
        resp_status = status.HTTP_302_FOUND
    else:
        User.objects.filter(id=user.id).update(username=data['username'])
        response['success'] = True
        response['username'] = user.username
        response['email'] = user.email
        resp_status = status.HTTP_200_OK
    return Response(response, status=resp_status)


# ------------------------
# Change password endpoint
# ------------------------


CHANGE_PASSWORD_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'old_password',
            required=True,
            location='form',
            schema=coreschema.String(description='Old password')
        ),
        coreapi.Field(
            'new_password',
            required=True,
            location='form',
            schema=coreschema.String(description='New password')
        )
    ]
)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@schema(CHANGE_PASSWORD_SCHEMA)
def change_password(request):
    """ Sets a new password given the old password

    ### Response

    * Status code 200

            {
                "success": <boolean: true>
            }

        * `success` - Whether the change request succeeded or not
    
    * Status code 400 (When old password is incorrect)

            {
                "success": <boolean: false>,
                "message": <string: "wrong_old_password">
            }
    """
    data = request.data
    response = {}
    user = User.objects.get(id=request.user.id)
    if user.check_password(data.get('old_password')):
        user.set_password(data.get('new_password'))
        user.save()
        response['success'] = True
        resp_status = status.HTTP_200_OK
    else:
        response['success'] = False
        response['message'] = 'wrong_old_password'
        resp_status = status.HTTP_400_BAD_REQUEST
    return Response(response, status=resp_status)


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
    """ Changes language preference

    ### Response

    * Status code 200

            {
                "success": <boolean>
            }

        * `success` - Whether the change request succeeded or not

    * Status code 400 (When old password is incorrect)

            {
                "success": <boolean: false>,
                "message": <string: "wrong_language">
            }
    """
    response = {'success': False}
    data = request.data
    user = request.user
    user_profile = user.profiles.first()
    language = data['language']
    if check_language_exists(language):
        user_profile.language = data['language']
        user_profile.save()
        response['success'] = True
        return Response(response)
    else:
        response['message'] = 'wrong_language'
        return Response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


# -----------------------
# Reset password endpoint
# -----------------------


RESET_PASSWORD_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'action',
            required=True,
            location='form',
            schema=coreschema.String(
                description='Action can either be `request`, `confirm`, or `change`'
            )
        ),
        coreapi.Field(
            'email',
            required=False,
            location='form',
            schema=coreschema.String(
                description='Registered email of the user'
            )
        ),
        coreapi.Field(
            'code',
            required=False,
            location='form',
            schema=coreschema.String(description='Code')
        ),
        coreapi.Field(
            'password',
            required=False,
            location='form',
            schema=coreschema.String(description='New password')
        )
    ]
)


@api_view(['POST'])
@schema(RESET_PASSWORD_SCHEMA)
def reset_password(request):
    """ Resets user's password

    ### Response

    **For `action == "request"`**

    The request requires `email` in the payload.

    * Status code 202 (When the reset request is accepted for processing)

            {
                "success": <boolean>
            }

        * `success` - Whether the change request is accepted or not

    * Status code 400 (When the email is not found)

            {
                "success": <boolean: false>,
                "message": <string: "user_not_found">
            }
    
    **For `action == "change"`**

    The request requires the `code` and `password` in the payload.

    * Status code 200 (When password has been changed)

            {
                "success": <boolean: true>
            }

    * Status code 400 (When the code is not correct)

            {
                "success": <boolean: false>,
                "message": <string: "user_not_found">
            }
    """
    response = {'success': False}
    data = request.data
    if data['action'] == 'request':
        try:
            user = User.objects.select_related(
                'profiles'
            ).get(email=data['email'])
            token_salt = generate_token_salt(user)
            user_profile = user.profiles.first()
            send_reset_password.delay(
                user.email, user.username, token_salt,
                user_profile.language
            )
            response['success'] = True
            resp_status = status.HTTP_202_ACCEPTED
        except User.DoesNotExist:
            resp_status = status.HTTP_400_BAD_REQUEST
            response['message'] = 'user_not_found'
    elif data['action'] == 'change':
        try:
            code = data['code']
            token = AuthToken.objects.get(salt=code)
            user = User.objects.get(id=token.user.id)
            user.set_password(data['password'])
            user.save()
            response['success'] = True
            resp_status = status.HTTP_200_OK
            token.delete()
        except AuthToken.DoesNotExist:
            response['message'] = 'wrong_code'
            resp_status = status.HTTP_400_BAD_REQUEST
    return Response(response, status=resp_status)


# ---------------------------
# Get signature code endpoint
# ---------------------------


GET_SIGCODE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'verificationCode',
            required=True,
            location='query',
            schema=coreschema.String(description='Verification code')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(GET_SIGCODE_SCHEMA)
def get_signature_code(request):
    """ Retrieves signature code

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "signature_code": <string>
            }

        * `success` - Whether the retrieve request succeeded or not
        * `signature_code` - The signature's BBCode

    * Status code 400

            {
                "success": <boolean: false>,
                "message": <string: "forum_profile_not_found">
            }

    """
    response = {'success': False}
    data = request.query_params
    vcode = data.get('verificationCode')
    try:
        forum_profile = ForumProfile.objects.get(verification_code=vcode)
        if config.TEST_MODE:
            sig_code = forum_profile.signature.test_signature
        else:
            sig_code = forum_profile.signature.code
        if config.ENABLE_CLICK_TRACKING:
            response['signature_code'] = inject_verification_code(sig_code, vcode)
        else:
            response['signature_code'] = sig_code
        response['success'] = True
        resp_status = status.HTTP_200_OK
    except ForumProfile.DoesNotExist:
        resp_status = status.HTTP_400_BAD_REQUEST
        response['message'] = 'forum_profile_not_found'
    return Response(response, status=resp_status)


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
    """ Checks if email exists

    ### Response

    * Status code 200

            {
                "success": <boolean>,
                "email_exists": <boolean>
            }

        * `success` - Whether the request has succeeded or not
        * `email_exists` - Whether the email exists in the DB or not
    """
    data = request.query_params
    response = {'success': True, 'email_exists': False}
    if data.get('email'):
        user_check = UserProfile.objects.filter(
            user__email__iexact=data.get('email').strip(),
            email_confirmed=True
        )
        if user_check:
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
    """ Checks if username exists

    ### Response

    * Status code 200

            {
                "success": <boolean>,
                "username_exists": <boolean>
            }

        * `success` - Whether the request has succeeded or not
        * `username_exists` - Whether the username exists in DB or not
    """
    data = request.query_params
    response = {'success': True, 'username_exists': False}
    if data.get('username'):
        user_check = User.objects.filter(username__iexact=data.get('username').strip())
        if user_check.exists():
            response['username_exists'] = True
    return Response(response)


# ----------------------
# Get langauges endpoint
# ----------------------


@api_view(['GET'])
def get_languages(request):
    """ Retrieves available languages

    ### Response

    * Status code 200

            [<array: Language>, <array: Language>, ...]

        <br>Each `Language` array contains the following info

            {
                "value": <string>,
                "text": <string>
            }

        * `value` - Language code (e.g. en, jp, fr)
        * `text` - Full language name (e.g. English, Japanese, French)
    """
    user_profile = request.user.profiles.first()
    with translation_on(user_profile.language):
        return Response(
            [
                {'value': language[0], 'text': str(language[1])}
                for language in settings.LANGUAGES
            ]
        )


# -------------------------
# Generate 2FA URI endpoint
# -------------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def generate_2fa_uri(request):
    """ Generates two-factor authentication URI

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "service": <string>,
                "account": <string>,
                "key": <string>,
                "uri": <string>
            }

        * `success` - Whether the request has succeeded or not
        * `service` - Name of the service (i.e. Volentix Venue)
        * `account` - User's email address
        * `key` - OTP key
        * `uri` - Complete OTP key details in URI format
    """
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
    """ Verifies two-factor auth OTP code
    
    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "verified": <boolean>
            }

        * `success` - Whether the request succeeded or not
        * `verified` - Whether the submitted OTP code is correct or not

    * Status code 400

            {
                "success": <boolean: false>
            }
    """
    response = {'success': False}
    resp_status = status.HTTP_400_BAD_REQUEST
    data = request.data
    profile = request.user.profiles.first()
    if profile:
        otp_secret = decrypt_data(profile.otp_secret, settings.SECRET_KEY)
        totp = pyotp.totp.TOTP(otp_secret)
        verified = totp.verify(data['otpCode'])
        if verified:
            if 'enable_2fa' in data.keys() and data['enable_2fa']:
                profile.enabled_2fa = True
                profile.save()
            response['verified'] = verified
            response['success'] = True
        else:
            response['verified'] = False
        resp_status = status.HTTP_200_OK
    return Response(response, status=resp_status)


# --------------------
# Disable 2FA endpoint
# --------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def disable_2fa(request):
    """ Disables two-factor authentication

    ### Response

    * Status code 200

            {
                "success": <boolean: true>
            }
    """
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


class NotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action_link = serializers.CharField(max_length=100)
    action_text = serializers.CharField(max_length=100)
    code = serializers.CharField(max_length=30)
    dismissible = serializers.BooleanField()
    text = serializers.CharField(max_length=200)
    variant = serializers.CharField(max_length=50)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_notifications(request):
    """ Retrieves notifications

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "notifications": <list: Notification>
            }

        * `success` - Whethere the request has succeeded or not
        * `notifications` - List of notifications

        Each `Notification` array contains the following info

            {
                "id": <int>,
                "action_link": <string>,
                "action_text": <string>,
                "code": <string>,
                "dismissibale": <boolean>,
                "text": <string>,
                "variant": <string>
            }

        * `id` - ID of the notification in the database
        * `action_link` - The action link notification button, if any
        * `action_text` - The text of the notification button, if any
        * `code` - Short code that identifies the kind of notification
        * `dismissible` - Whether the notification can be dismissed or not
        * `text` - The notification message text
        * `variant` - The variant of the notification alert
          (`primary`, `info`, `success`, `warning`, `danger`)
    """
    response = {}
    profile = request.user.profiles.first()
    notifs = Notification.objects.filter(active=True).exclude(
        dismissed_by=request.user
    )
    if profile.enabled_2fa:
        notifs = notifs.exclude(code='2fA_notification')
    serializer = NotificationSerializer(notifs, many=True)
    response['notifications'] = serializer.data
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
    """ Dismisses a notification

    ### Response

    * Status code 200 (When the notification is successsfully dismissed)

            {
                "success": <boolean: true>
            }

        * `success` - Whether the dismissal request succeeded or not

    * Status code 400 (When the notification ID cannot be found)

            {
                "success": <boolean: false>,
                "message": <string: "notification_not_found">
            }
        
        * `message` - Error message, when success is false
    """
    response = {'success': False}
    data = request.data
    try:
        notif = Notification.objects.get(id=data['notificationId'])
        notif.dismissed_by.add(request.user)
        response['success'] = True
        resp_status = status.HTTP_200_OK
    except Notification.DoesNotExist:
        resp_status = status.HTTP_400_BAD_REQUEST
        response['message'] = 'notification_not_found'
    return Response(response, status=resp_status)


# ------------------------
# Get forum sites endpoint
# ------------------------


class ForumSiteSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField(max_length=50)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_forum_sites(request):
    """ Retrieves list of forum sites

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "forum_sites": <list: ForumSite>
            }

        * `success` - Whether the request succeeded or not
        * `forum_sites` - List of forum sites

        Each `ForumSite` array contains the following info

            {
                "id": <int>,
                "name": <string>
            }

        * `id` - ID of the forum site in the database
        * `name` - Name of the forum site

    * Status code 404 (When no forum sites were found)

            {
                "success": <boolean: false>,
                "message": <string: "forum_sites_not_found">
            }

        * `message` - Error message, when success is false
    """
    response = {'success': False}
    sites = ForumSite.objects.all()
    if sites.count():
        serializer = ForumSiteSerializer(sites, many=True)
        response['forum_sites'] = serializer.data
        response['success'] = True
        resp_status = status.HTTP_200_OK
    else:
        resp_status = status.HTTP_400_BAD_REQUEST
        response['message'] = 'forum_sites_not_found'
    return Response(response, status=resp_status)


# -----------------------------
# Create forum profile endpoint
# -----------------------------


CREATE_FORUM_PROFILE_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_user_id',
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


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(CREATE_FORUM_PROFILE_SCHEMA)
def create_forum_profile(request):
    """ Creates a forum profile

    ### Response

    * Status code 201 (When forum profile is created)

            {
                "success": <boolean: true>,
                "id": <int>
            }

    * Status code 200 (When forum profile already exists)

            {
                "success": <boolean: true>,
                "exists": <boolean: true>,
                "verified": <boolean>,
                "id": <int>
            }

    * Status code 400 (When the forum profile cannot be created)

            {
                "success": <boolean: false>,
            }
    """
    data = request.data
    response = {'success': False}
    forum_id = data.get('forum_id')
    if str(forum_id) == '1':
        forum_site = ForumSite.objects.get(name='bitcointalk.org')
        forum_id = str(forum_site.id)
    forum = ForumSite.objects.get(id=forum_id)
    # TODO -- Reflect the accurate status of the checking
    info = get_user_position(
        forum_id,
        data['forum_user_id'],
        request.user.id
    )
    if info['found']:
        profile_check = ForumProfile.objects.filter(
            forum_user_id=info['forum_user_id'],
            verified=True,
            forum=forum
        )
        if profile_check.exists():
            resp_status = status.HTTP_200_OK
            response['exists'] = True
            response['verified'] = True
        else:
            rank, created = ForumUserRank.objects.get_or_create(
                name=info['position'],
                forum_site=forum
            )
            del created
            if rank.allowed or config.TEST_MODE:
                resp_status = status.HTTP_201_CREATED
                user_profile = UserProfile.objects.get(user=request.user)
                fp_object = ForumProfile(
                    user_profile=user_profile,
                    forum_user_id=info['forum_user_id'],
                    forum_username=info['forum_user_name'],
                    forum=forum,
                    forum_rank=rank,
                    active=True,
                    verification_code=shortuuid.ShortUUID().random(length=8)
                )
                fp_object.save()
                response['id'] = fp_object.id
                response['success'] = True
                # Trigger the task to adjust the scraping rate
                set_scraping_rate.delay()
            else:
                resp_status = status.HTTP_403_FORBIDDEN
                response['error_code'] = 'insufficient_forum_position'
    else:
        response['error_code'] = 'user_not_found_in_forum_site'
        resp_status = status.HTTP_400_BAD_REQUEST
    return Response(response, status=resp_status)


# ---------------------------
# Get forum profiles endpoint
# ---------------------------


class ForumProfileSerializer(serializers.Serializer):
    id = serializers.CharField()
    forum_user_id = serializers.CharField()


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
            required=False,
            location='query',
            schema=coreschema.String(description='Forum user ID')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(GET_FORUM_PROFILES_SCHEMA)
def get_forum_profiles(request):
    """ Retrieves forum profiles

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "forum_profiles": <list: ForumProfile>
            }

        * `success` - Whether the retrieve request succeeded or not

        Each `ForumProfile` array contains the following info

            {
                "id": <int>,
                "forum_user_id": <int>
            }

        * `id` - ID of the forum profile in the database
        * `forum_user_id` - ID of the user in the forum site

    * Status code 400

            {
                "success": <boolean: false>,
                "message": <string: "forum_profiles_not_found">
            }

        * `message` - Error message, when success if false
    """
    data = request.query_params
    response = {'success': False}
    forum_id = data.get('forum_id')
    resp_status = status.HTTP_400_BAD_REQUEST
    try:
        if str(forum_id) == '1':
            forum_site = ForumSite.objects.get(name='bitcointalk.org')
            forum_id = str(forum_site.id)
        forum_profiles = ForumProfile.objects.filter(
            forum_id=forum_id,
            user_profile__user=request.user
        )
        if data.get('forum_user_id'):
            forum_profiles = forum_profiles.filter(
                forum_user_id=data.get('forum_user_id')
            )
        if forum_profiles:
            response['success'] = True
            serializer = ForumProfileSerializer(forum_profiles, many=True)
            response['forum_profiles'] = serializer.data
            resp_status = status.HTTP_200_OK
        else:
            resp_status = status.HTTP_400_BAD_REQUEST
            response['message'] = 'forum_profiles_not_found'
    except ValidationError:
        response['message'] = 'forum_profiles_not_found'
        resp_status = status.HTTP_400_BAD_REQUEST
    finally:
        return Response(response, status=resp_status)


# -----------------------
# Get signatures endpoint
# -----------------------


def inject_verification_code(sig_code, verification_code):
    """ Helper function for injecting verification code to signature """

    def repl(m):
        return '%s?vcode=%s' % (m.group(), verification_code)

    if 'http' in sig_code:
        pattern = r'http[s]?://([a-z.])*volentix([a-z./-?=&])+'
        return re.sub(pattern, repl, sig_code)
    elif 'link' in sig_code:
        return sig_code + '?vcode=' + verification_code
    else:
        return sig_code


class SignatureSerializer(serializers.Serializer):
    id = serializers.CharField()
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
            location='query',
            schema=coreschema.String(description='Forum site ID')
        ),
        coreapi.Field(
            'forum_user_rank',
            required=False,
            location='query',
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
            schema=coreschema.Boolean(description='Get own signatures')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(GET_SIGNATURES_SCHEMA)
def get_signatures(request):
    """ Retrives list of signatures

    ### Response

    * Status code 200

            {
                "success": <boolean: true>,
                "signatures": <list: Signature>
            }

        <br>Each `Signature` array contains the following info

            {
                "id": <int>,
                "name": <string>,
                "image": <string>,
                "code": <string>,
                "verification_code": <string>,
                "usage_count": <int>,
                "forum_site_name": <string>,
                "forum_user_name": <string>,
                "forum_userid": <string>
            }

    """
    data = request.query_params
    response = {'success': False}
    if data.get('own_sigs') == '1' or data.get('own_sigs') == 'true':
        forum_profiles = ForumProfile.objects.filter(
            user_profile__user=request.user,
            verified=True
        )
        signatures = Signature.objects.filter(
            id__in=forum_profiles.values_list('signature_id', flat=True)
        )
        fp_map = {x.signature.id: x.id for x in forum_profiles}
    else:
        forum_id = data.get('forum_site_id')
        if str(forum_id) == '1':
            forum_site = ForumSite.objects.get(name='bitcointalk.org')
            forum_id = str(forum_site.id)
        signatures = Signature.objects.filter(
            forum_site_id=forum_id,
        )
        if not config.TEST_MODE and data.get('forum_user_rank'):
            signatures = signatures.filter(
                user_ranks__name=data.get('forum_user_rank')
            )
    forum_profile = None
    if data.get('forum_profile_id'):
        forum_profile = ForumProfile.objects.get(
            id=data.get('forum_profile_id')
        )
    if not data.get('forum_user_rank') and forum_profile:
        if forum_profile.forum_rank:
            signatures = signatures.filter(
                user_ranks__in=[forum_profile.forum_rank]
            )
    if signatures.count():
        for sig in signatures:
            if config.TEST_MODE:
                sig_code = sig.test_signature
            else:
                sig_code = sig.code
            if not forum_profile:
                forum_profile = ForumProfile.objects.get(
                    id=fp_map[sig.id]
                )
            verification_code = forum_profile.verification_code
            if config.ENABLE_CLICK_TRACKING:
                sig.code = inject_verification_code(
                    sig_code,
                    verification_code
                )
            else:
                sig.code = sig_code
            # sig.image = '%s/media/%s' % (settings.VENUE_DOMAIN, sig.image)
            sig.usage_count = sig.users.count()
            sig.verification_code = verification_code
            sig.forum_site_name = forum_profile.forum.name
            sig.forum_user_name = forum_profile.forum_username
            sig.forum_userid = forum_profile.forum_user_id
        response['success'] = True
    serializer = SignatureSerializer(signatures, many=True)
    response['signatures'] = serializer.data
    return Response(response)


# -------------------------
# Points breakdown endpoint
# -------------------------


def build_bonus_points_data(rank, posts):
    bonus_pct = posts.latest().influence_bonus_pct
    bonus_pts = posts.aggregate(Sum('influence_bonus_pts'))
    bonus_pts = bonus_pts['influence_bonus_pts__sum']
    data = {
        'position': rank.name,
        'num_posts': posts.count(),
        'bonus_percentage': bonus_pct,
        'total_bonus_points': bonus_pts
    }
    return data


POINTS_BREAKDOWN_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'forum_id',
            required=False,
            location='query',
            schema=coreschema.String(description='Forum ID')
        )
    ]
)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@schema(POINTS_BREAKDOWN_SCHEMA)
def get_points_breakdown(request):
    """ Retrives points/rewards breakdown

    ### Response

    * Status code 200

            {
                "sitewide_stats": {
                    "total_posts": <int>,
                    "total_post_points": <int>,
                    "total_bonus_points": <int>,
                    "bonus_points": <list: PostBonus>
                },
                "settings": {
                    "post_points_multiplier": <int>,
                    "maturation_period": <int>
                },
                "user_stats": {
                    "current_forum_position": <string>,
                    "total_posts": <int>,
                    "total_post_points": <int>,
                    "total_bonus_points": <int>,
                    "bonus_points": <list: PostBonus>,
                    "upcoming_posts": <int>,
                    "upcoming_post_points": <int>,
                    "upcoming_bonus_poitns": <int>
                }
            }

        * `sitewide_stats` - Stats for the whole site
        * `total_posts` - Total number of posts
        * `total_post_points` - Sum of all points
        * `total_bonus_points` - Sum of all bonus points
        * `bonus_points` - List of bonuses per forum rank/position
        * `settings` - Global settings of the point system
        * `post_points_multiplier` - Number of points per post
        * `maturation_period` - Waiting period before points are credited
        * `user_stats` - Stats for the requesting user
        * `current_forum_position` - Current forum position/rank
        * `upcoming_posts` - Posts that might get credited upon maturation
        * `upcoming_post_points` - Anticipated post points of upcoming posts
        * `upcoming_bonus_points` - Anticipated bonus points of upcoming posts

        <br>Each `PostBonus` array contains the following info

            {
                "position": <string>,
                "num_posts": <int>,
                "bonus_percentage": <int>,
                "total_bonus_points": <int>
            }

        * `position` - Forum user position/rank
        * `num_posts` - Number of posts
        * `bonus_percentage` - Percentage of post points to give as bonus
        * `total_bonus_points` - Sum of bonus points of the num_posts
    """
    stats = {}
    # Get the forum site
    forum_id = request.query_params.get('forum_id')
    if not forum_id or forum_id == '1':
        forum_site = ForumSite.objects.get(name='bitcointalk.org')
        forum_id = str(forum_site.id)
    try:
        forum = ForumSite.objects.get(id=forum_id)
        # Get global settings
        stats['settings'] = {
            'post_points_multiplier': config.POST_POINTS_MULTIPLIER,
            'maturation_period': config.MATURATION_PERIOD
        }
        # Get sum of all post points
        credited_posts = ForumPost.objects.filter(credited=True)
        sum_base_points = credited_posts.aggregate(Sum('base_points'))
        sum_base_points = sum_base_points['base_points__sum']
        # Get sum of all bonus points
        sum_bonus_points = credited_posts.aggregate(Sum('influence_bonus_pts'))
        sum_bonus_points = sum_bonus_points['influence_bonus_pts__sum']
        stats['sitewide_stats'] = {
            'total_posts': credited_posts.count(),
            'total_post_points': sum_base_points,
            'total_bonus_points': sum_bonus_points
        }
        # Get user posts
        user_profile = UserProfile.objects.get(user=request.user)
        user_posts = ForumPost.objects.filter(user_profile=user_profile)
        # Get user's credited posts
        credited = user_posts.filter(credited=True)
        credited_post_pts = credited.aggregate(Sum('base_points'))
        credited_post_pts = credited_post_pts['base_points__sum']
        credited_bonus_pts = credited.aggregate(Sum('influence_bonus_pts'))
        credited_bonus_pts = credited_bonus_pts['influence_bonus_pts__sum']
        # Get user's uncredited posts
        uncredited = user_posts.filter(credited=False, matured=False)
        uncredited_post_pts = uncredited.aggregate(Sum('base_points'))
        uncredited_post_pts = uncredited_post_pts['base_points__sum']
        uncredited_bonus_pts = uncredited.aggregate(Sum('influence_bonus_pts'))
        uncredited_bonus_pts = uncredited_bonus_pts['influence_bonus_pts__sum']
        # Get user-level stats
        forum_profile = ForumProfile.objects.filter(
            user_profile=user_profile,
            forum=forum
        )
        forum_position = forum_profile.first().forum_rank.name
        stats['user_stats'] = {
            'current_forum_position': forum_position,
            'total_posts': credited.count(),
            'total_post_points': credited_post_pts or 0,
            'total_bonus_points': credited_bonus_pts or 0,
            'upcoming_posts': uncredited.count(),
            'upcoming_post_points': uncredited_post_pts or 0,
            'upcoming_bonus_poitns': uncredited_bonus_pts or 0,
        }
        # Get the details of the bonus points
        sitewide_bonus_points = []
        user_bonus_points = []
        ranks = ForumUserRank.objects.filter(
            forum_site=forum
        )
        for rank in ranks:
            # Sitewide bonus points
            posts = ForumPost.objects.filter(
                forum_rank=rank,
                credited=True
            )
            if posts.count():
                data = data = build_bonus_points_data(rank, posts)
                sitewide_bonus_points.append(data)
            # User's bonus points
            posts = ForumPost.objects.filter(
                user_profile=user_profile,
                forum_rank=rank,
                credited=True
            )
            if posts.count():
                data = build_bonus_points_data(rank, posts)
                user_bonus_points.append(data)
        stats['sitewide_stats']['bonus_points'] = sitewide_bonus_points
        stats['user_stats']['bonus_points'] = user_bonus_points
        return Response(stats)
    except ForumSite.DoesNotExist:
        response = {'error_code': 'forum_site_not_found'}
        return Response(response, status.HTTP_400_BAD_REQUEST)


# ------------------------
# Referrals views
# ------------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_information_about_referrals(request):
    """ Retrieves information about referrals

        ### Response

        * Status code 200

                {
                    "referrals": [
                        {
                            "user_id" : <string>,
                            "username": <string>,
                            "amount": <float>
                        },
                        ...
                    ]
                }
            * `referrals` - an array with information about all the
                            referrals
                * `user_id` - UUID of the user's profile
                * `username` - Registered username
                * `amount` - Amount of bonuses from this referral (0 if signature is not verified)

            <br>If user doesn't have referrals response will be:

                {
                    "referrals": []
                }

        """
    user_profile = request.user.profiles.last()
    referrals_from_db = user_profile.referrals.order_by(
        'created_at'
    ).values(
        'bonus', 'referral__user__username', 'referral__id'
    )
    referrals = [
        {
            'user_id': referral['referral__id'],
            'username': referral['referral__user__username'],
            'amount': referral['bonus']
        }
        for referral in referrals_from_db
    ]
    return Response({'referrals': referrals})


SEND_EMAILS_SCHEMA = AutoSchema(
    manual_fields=[
        coreapi.Field(
            'emails',
            required=True,
            location='form',
            schema=coreschema.Array(description='A list of email'),
            type='array',
            description='A list of email',
            example='["some@email.com", "some@email2.com", "some@email2.com"]'
        )
    ]
)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@schema(SEND_EMAILS_SCHEMA)
def send_emails_with_referral_code(request):
    """ Send email with referral code. <br>
    At least one field (`email` or `emails`) should be filled.

    ### Response

    * Status code `200` (at least one message was sent)

            {
                "success": <boolean: true>,
                "message": <str>
            }

        * `success` - Result of the request (true)
        * `message` - Information about the result


    * Status code `422` (wrong payload structure is provided)

            {
                "success": <boolean: false>,
                "message": <str>
            }

        * `success` - Result of the request (false)
        * `message` - Error description

    """
    # group all emails to one list
    emails = request.data.get('emails', [])

    if not isinstance(emails, (list, tuple)):
        return Response(
            {
                'result': True,
                'message': "'emails' should be a list not {} type".format(type(emails))
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    # if emails list is empty return 422
    if not emails:
        return Response(
            {
                'result': True,
                'message': 'at least one email address is required'
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    # if there is at least on email treat it and prepare to send
    emails = ','.join([e.lower().strip() for e in emails if e])
    try:
        # try to send it
        # use the same language code for emails as for a current user
        user_profile = request.user.profiles.first()
        emails_result = send_email(
            template='venue/email_referral.html',
            email=emails,
            language=user_profile.language,
            subject='Referral to Volentix Bitcointalk.org signature campaign',
            code=user_profile.referral_code,
            referrer_name=request.user.username,
            user_lang=user_profile.language
        )
        response_result = not emails_result.get('ErrorCode')
        # 200 if `ErrorCode` in payload == 0 else 422
        response_status_code = (status.HTTP_200_OK
                                if response_result
                                else status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(
            {
                'result': response_result,
                'message': emails_result.get('Message', '')
            },
            status=response_status_code
        )
    except Exception as e:
        # 422 if there is some troubles with email sending
        return Response(
            {
                'result': False,
                'message': str(e)
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


ASSIGN_VERTO_ADDRESS_SCHEMA = AutoSchema(
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
        ),
        coreapi.Field(
            'verto_address',
            required=True,
            location='form',
            schema=coreschema.String(description='Verto address')
        )
    ]
)


@api_view(['POST'])
@schema(ASSIGN_VERTO_ADDRESS_SCHEMA)
def assign_verto_address(request):
    data = request.data
    response = {'success': False}
    error_code = 'unknown_error'
    resp_status = status.HTTP_400_BAD_REQUEST
    try:
        verto_address = data['verto_address']
        username = data['username']
        password = data['password']
    except KeyError:
        response['error_code'] = 'wrong_credentials'
        return Response(response, status=resp_status)
    try:
        if '@' in data['username']:
            user = User.objects.get(
                email__iexact=username
            )
        else:
            user = User.objects.get(
                username__iexact=data['username']
            )
        pass_check = user.check_password(password)
        if pass_check:
            if user.is_active:
                profile = user.profiles.first()
                proceed = False
                if profile.email_confirmed:
                    proceed = True
                else:
                    error_code = 'email_verification_required'
                    resp_status = status.HTTP_403_FORBIDDEN
                if proceed:
                    user_profile = user.profiles.first()
                    try:
                        user_profile.verto_address = verto_address
                        user_profile.save()
                        response = {'success': True}
                        resp_status = status.HTTP_200_OK
                    except IntegrityError:
                        error_code = 'verto_address_not_unique'
            else:
                error_code = 'user_deactivated'
                resp_status = status.HTTP_403_FORBIDDEN
        else:
            error_code = 'wrong_credentials'
    except User.DoesNotExist:
        error_code = 'wrong_credentials'
    if not response['success']:
        response['error_code'] = error_code
    return Response(response, status=resp_status)


# ------------------------
# Debugging view functions
# ------------------------


def trigger_data_update(request):
    update_data.delay()
    return Response({'success': True})


def check_task_status(request, task_id):
    task = AsyncResult(task_id)
    return Response({'status': task.status})
