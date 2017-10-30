from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from venue.models import UserProfile
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
            'email': token.user.email
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