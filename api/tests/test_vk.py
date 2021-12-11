from server.config import config
from tests.test_common import *


def test_version():
    assert client.get("/").status_code == 200
    assert client.get("/version").status_code == 200
    version = client.get("/version").text
    assert version == config['VERSION']


url = '/vk/user/'


def test_unknown_plugin():
    assert make_api_request(url, 'abc', ['abcd'], extract_json=False).status_code == 400


# Main tested vk user. Should not change page info
user_vk = 'ffboris'
# Actual IG of user_vk
user_ig = 'fiobond'


def test_vk_basic():
    data = make_api_request(url, user_vk, ['user'])
    assert data['user']['valid']


def test_vk_all_options():
    options = ['user', 'user-describe', 'user-friends']
    data = make_api_request(url, user_vk, options)
    assert all([option in data for option in options])


def test_find_instagram():
    options = ['find-instagram']
    data = make_api_request(url, user_vk, options)
    assert user_ig in ','.join(data['find-instagram'])




