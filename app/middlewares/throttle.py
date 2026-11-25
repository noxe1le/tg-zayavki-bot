import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class ThrottleMiddleware(BaseMiddleware):
    """Гасит повторные нажатия и флуд от одного пользователя.

    Хранит время последнего события в памяти: для одного процесса этого достаточно,
    при переходе на несколько воркеров надо выносить в Redis.
    """

    def __init__(self, rate: float = 0.7) -> None:
        self._rate = rate
        self._last: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        if now - self._last.get(user.id, 0.0) < self._rate:
            if isinstance(event, CallbackQuery):
                await event.answer("Слишком часто, подождите секунду", show_alert=False)
            elif isinstance(event, Message):
                return None
            return None

        self._last[user.id] = now
        return await handler(event, data)
