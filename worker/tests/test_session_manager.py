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
    assert len(manager._active_sessions) == count
    await manager.stop()


@pytest.mark.asyncio
async def test_using_count_sessions(postgres):
    manager = SessionManager(key_type='ig', controller=IgApiSession, requests_delay_min=10, requests_delay_max=30)
    for i in range(3):
        async with await manager.get() as api:
            await api.get_following(8368846410, count=10, end_cursor='')
    assert len(manager._active_sessions) == 4
    await manager.stop()

