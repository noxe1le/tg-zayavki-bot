import pytest

from app.db.base import Database
from app.db.repository import RequestRepository


@pytest.fixture
async def repo(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.init()
    yield RequestRepository(db)
    await db.close()


async def test_add_and_read(repo: RequestRepository) -> None:
    created = await repo.add(
        user_id=1, username="ivan", name="Иван", phone="+79001234567", comment="нужен бот"
    )
    assert created.id == 1
    items = await repo.by_user(1)
    assert len(items) == 1
    assert items[0].phone == "+79001234567"
    assert items[0].username == "ivan"


async def test_isolated_by_user(repo: RequestRepository) -> None:
    await repo.add(user_id=1, username=None, name="А", phone="+79001112233", comment="первая")
    await repo.add(user_id=2, username=None, name="Б", phone="+79001112244", comment="вторая")
    assert await repo.count(1) == 1
    assert await repo.count() == 2
    assert [i.name for i in await repo.by_user(2)] == ["Б"]


async def test_pagination(repo: RequestRepository) -> None:
    for i in range(7):
        await repo.add(
            user_id=1, username=None, name=f"Клиент {i}", phone="+79001112233", comment="задача"
        )
    first = await repo.by_user(1, limit=5, offset=0)
    second = await repo.by_user(1, limit=5, offset=5)
    assert len(first) == 5
    assert len(second) == 2
    assert first[0].name == "Клиент 6"


def test_short_comment() -> None:
    from datetime import datetime

    from app.models import Request

    long_request = Request(
        id=1, user_id=1, username=None, name="А", phone="+79001112233",
        comment="а" * 100, created_at=datetime.now(),
    )
    assert long_request.short_comment.endswith("...")
    assert len(long_request.short_comment) == 80
