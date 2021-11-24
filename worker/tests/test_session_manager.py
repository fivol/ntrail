import pytest

from worker.credentials.models import bind, db
from worker.parsers.ig.ig import IgApiSession
from worker.session.session_manager import SessionManager
from worker.credentials.credentials import Credentials, AccessModel


@pytest.fixture()
async def postgres():
    await bind()
    return db


@pytest.fixture()
def api():
    return SessionManager(key_type='ig', controller=IgApiSession, requests_delay_min=10, requests_delay_max=30)


@pytest.mark.asyncio
@pytest.mark.parametrize('count', range(1, 10))
async def test_add_session(count, postgres):
    manager = SessionManager(key_type='ig', controller=IgApiSession, requests_delay_min=10, requests_delay_max=30)
    assert await manager._receive_keys(count)
    assert len(manager._all_sessions) == count
    assert len(manager._active_sessions) == count
    for session in manager._all_sessions:
        assert session in manager._active_sessions

    await manager.stop()


