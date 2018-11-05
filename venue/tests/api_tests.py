from venue.views import assign_verto_address
from venue.models import UserProfile
import pytest


@pytest.mark.django_db
def test_assign_verto_address(rf):
    payload = {
        'username': 'thor',
        'password': 'default2018',
        'verto_address': 'xxx'
    }
    request = rf.post('/internal/api/assign-verto-address', payload)
    response = assign_verto_address(request)
    assert response.status_code == 200
    user = UserProfile.objects.get(
        user__username='thor'
    )
    assert user.verto_address == 'xxx'
