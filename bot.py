import asyncio
import logging

from aiogram import Bot, Dispatcher

import db
from config import load_config
from handlers.admin_handlers import router as admin_router
from handlers.user_handlers import forwarded_map, restore_reminders, router as user_router, start_daily_digest
from i18n import load_langs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    cfg = load_config()

    await db.init_db()
    logger.info("БД инициализирована")

    await load_langs()
    forwarded_map.update(await db.get_all_forwarded())
    logger.info("Кэши загружены из БД")

    bot = Bot(token=cfg.bot_token)
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)

    await restore_reminders(bot)
    start_daily_digest(bot)

    logger.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
