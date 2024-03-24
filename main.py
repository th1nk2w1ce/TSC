import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.exc import IntegrityError

from config_reader import config
from DB.models import async_main
from DB.db_requests import Storage
import throttling_middleware as throttle_middleware
from Handlers import main_menu, buy_ts, change_ts, stake_sts, unstake_sts


async def main() -> None:
    await async_main()
    try:
        await Storage(2123712526).add_user(2123712526, 'UQCgwAo8nuOwUiAyJB34WleDdt0HvFbMfD99TeT4U-REfEDx')
    except IntegrityError:
        pass
    default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=config.bot_token.get_secret_value(), default=default)
    dp = Dispatcher()
    dp.callback_query.middleware.register(throttle_middleware.ThrottleMiddleware())
    dp.include_routers(main_menu.router, buy_ts.router, change_ts.router, stake_sts.router, unstake_sts.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
