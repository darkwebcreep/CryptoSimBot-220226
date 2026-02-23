# middlewares.py
import time
import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Any, Awaitable, Callable, Dict
from database import get_user, user_exists

logger = logging.getLogger(__name__)

# ==================== АНТИ-СПАМ MIDDLEWARE ====================

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


# ==================== АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЕЙ ====================

class AuthMiddleware(BaseMiddleware):
    """Middleware для автоматической регистрации пользователей при любом действии"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        user_id = user.id
        username = user.username
        first_name = user.first_name
        
        # Проверяем существование пользователя
        if not user_exists(user_id):
            logger.info(f"👤 Автоматическая регистрация пользователя {user_id} (@{username})")
            user_data = get_user(user_id, username, first_name)
            if user_data:
                logger.info(f"✅ Пользователь {user_id} успешно зарегистрирован")
            else:
                logger.error(f"❌ Ошибка регистрации пользователя {user_id}")
                if isinstance(event, Message):
                    await event.answer("❌ Ошибка регистрации. Попробуй /start")
                return
        else:
            logger.debug(f"✅ Пользователь {user_id} уже в БД")
        
        return await handler(event, data)


# ==================== ЛОГИРОВАНИЕ ЗАПРОСОВ ====================

class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех запросов"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        username = event.from_user.username or event.from_user.first_name
        text = event.text or "[не текст]"
        
        logger.info(f"📨 [{username}] ({user_id}): {text}")
        
        start_time = time.time()
        result = await handler(event, data)
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(f"📨 Ответ отправлен за {execution_time:.1f}ms")
        
        return result
