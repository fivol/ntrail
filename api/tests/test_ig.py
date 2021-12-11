from tests.test_common import *

url = '/ig/user/'

user = 'fiobond'


def test_ig_user_resolve():
    data = make_api_request(url, user, ['user'])
    assert data['user']['username'] == user


def test_ig_fans():
    data = make_api_request(url, user, ['user-fans'])
    print('data', data)
    assert len(data['user-fans']) > 0
