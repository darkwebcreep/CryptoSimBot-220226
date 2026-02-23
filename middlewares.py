# middlewares.py
import time
import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Any, Awaitable, Callable, Dict

logger = logging.getLogger(__name__)

class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, rate_limit=0.3):
        self.rate_limit = rate_limit
        self.last_time = {}
        logger.info(f"⚡ Анти-спам middleware: лимит {rate_limit} сек")
        
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        username = event.from_user.username or event.from_user.first_name
        current_time = time.time()
        
        if user_id in self.last_time:
            time_diff = current_time - self.last_time[user_id]
            if time_diff < self.rate_limit:
                logger.warning(f"⚠️ Спам от {username} (ID: {user_id})")
                if isinstance(event, Message):
                    await event.answer(f"⏳ Слишком часто! Подожди немного")
                return
        
        self.last_time[user_id] = current_time
        return await handler(event, data)