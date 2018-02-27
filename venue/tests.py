from django.test import TestCase
from venue.models import ForumSite, Language
from venue.scrapers import bitcoin_forum as btforum
from venue.scrapers import bitcointalk as bttalk
from rest_framework.test import APIClient
import pytest


@pytest.mark.django_db
@pytest.fixture()
def save_forum_sites():
    forum_sites = [
        {
            'name': 'bitcointalk.org',
            'address': 'https://bitcointalk.org',
            'scraper_name': 'bitcointalk.py'
        },
        {
            'name': 'forum.bitcoin.com',
            'address': 'https://forum.bitcoin.com',
            'scraper_name': 'bitcoin_forum.py'
        }
    ]
    for site in forum_sites:
        forum_site = ForumSite(**site)
        forum_site.save()
    forum_sites = ForumSite.objects.all()


@pytest.mark.django_db
def test_forum_sites_access(save_forum_sites):
    forum_sites = ForumSite.objects.all()
    assert forum_sites.count() == 2


def test_frontend_app_view(client):
    response = client.get('/')
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.fixture()
def save_languages():
    languages = [
        {'name': 'English', 'code': 'en'},
        {'name': 'Japanese', 'code': 'jp'}
    ]
    for language in languages:
        lang = Language(**language)
        lang.save()


@pytest.mark.django_db
@pytest.fixture()
def test_create_user_view(save_languages):
    client = APIClient()
    data = {
        'email': 'admin@example.com',
        'username': 'admin_user',
        'password': 'default2018',
        'language': 'en'
    }
    response = client.post('/create-user/', data, format='json')
    assert response.status_code == 200
    assert response.json()['status'] == 'success'
    assert 'token' in response.json()['user'].keys()
    return response.json()


@pytest.mark.django_db
def test_get_user(test_create_user_view):
    token = test_create_user_view['user']['token']
    client = APIClient()
    response = client.post('/get-user/', {'token': token}, format='json')
    assert response.status_code == 200
    assert response.json()['username'] == 'admin_user'