import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.config import config


client = TestClient(app)


def test_version():
    assert client.get("/").status_code == 200
    assert client.get("/version").status_code == 200
    version = client.get("/version").text
    assert version == config['VERSION']


def make_vk_api_request(user, options, extract_json=True):
    response = client.get('/vk/user/', params={'user': user, 'options': options})
    if not extract_json:
        return response
    assert response.status_code == 200
    return response.json()


def test_unknown_plugin():
    assert make_vk_api_request('abc', ['abcd'], extract_json=False).status_code == 400


# Main tested vk user. Should not change page info
user_vk = 'ffboris'
# Actual IG of user_vk
user_ig = 'fiobond'


def test_vk_basic():
    data = make_vk_api_request(user_vk, ['user'])
    assert data['user']['valid']


def test_vk_all_options():
    options = ['user', 'user-describe', 'user-friends']
    data = make_vk_api_request(user_vk, options)
    assert all([option in data for option in options])


def test_find_instagram():
    options = ['find-instagram']
    data = make_vk_api_request(user_vk, options)
    assert user_ig in ','.join(data['find-instagram'])


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    client.__enter__()
    yield
    client.__exit__()

