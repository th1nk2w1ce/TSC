from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from cachetools import TTLCache


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5) -> None:
        self.cache = TTLCache(maxsize=10_000, ttl=rate_limit)

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: CallbackQuery,
                       data: Dict[str, Any]
                       ) -> Any:
        
        if event.message.chat.id in self.cache:
            return

        self.cache[event.message.chat.id] = True
        return await handler(event, data)
