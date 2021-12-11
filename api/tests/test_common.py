import pytest as pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def make_api_request(url, user, options, extract_json=True):
    response = client.get(url, params={'user': user, 'options': options})
    if not extract_json:
        return response
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    client.__enter__()
    yield
    client.__exit__()
