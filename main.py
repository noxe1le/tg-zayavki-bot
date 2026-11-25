import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings
from app.db.base import Database
from app.db.repository import RequestRepository
from app.handlers import common, requests
from app.middlewares.throttle import ThrottleMiddleware

log = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()

    db = Database(settings.db_path)
    await db.init()
    repo = RequestRepository(db)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    throttle = ThrottleMiddleware(rate=settings.throttle_rate)
    dp.message.middleware(throttle)
    dp.callback_query.middleware(throttle)

    dp.include_routers(common.router, requests.router)
    dp["repo"] = repo
    dp["settings"] = settings

    log.info("запускаю polling")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        log.info("остановлен")


if __name__ == "__main__":
    main()
