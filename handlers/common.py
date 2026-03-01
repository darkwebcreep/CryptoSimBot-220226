# handlers/common.py
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime

from database import get_user, get_balance, get_user_skin, get_top_users, get_user_miners, get_user_owned_skins, update_balance
from config import CURRENCIES, ADMIN_ID, MINERS, SKINS
from ui_utils import create_header, create_section, create_footer, create_top_list, create_wallet_info

logger = logging.getLogger(__name__)

router = Router()

async def get_menu_for_user(user_id):
    """Возвращает нужное меню в зависимости от того, админ ли пользователь"""
    if user_id == ADMIN_ID:
        from keyboards import admin_keyboard
        return admin_keyboard()
    else:
        from keyboards import main_menu
        return main_menu()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    user_id = user.id
    
    # Логируем
    logger.info(f"👤 /start от пользователя {user_id} (@{user.username})")
    
    # Получаем или создаем пользователя
    user_data = get_user(user_id, user.username, user.first_name)
    
    # Получаем баланс ДО начисления
    old_balance = get_balance(user_id, 'ledoge')
    
    # ПРОВЕРЯЕМ И НАЧИСЛЯЕМ БОНУС
    bonus_given = False
    if old_balance == 0:
        # Начисляем стартовый бонус 1000 LEDOGE
        update_balance(user_id, 'ledoge', 1000, 'add')
        new_balance = get_balance(user_id, 'ledoge')
        logger.info(f"💰 Начислен стартовый бонус 1000 LEDOGE пользователю {user_id}")
        bonus_given = True
    else:
        new_balance = old_balance
    
    # Проверяем флаг перезагрузки
    is_after_reset = False
    try:
        from database import execute_query
        # Проверяем существование таблицы settings
        try:
            reset_flag = execute_query('SELECT value FROM settings WHERE key = "reset_occurred"', fetch_one=True)
            if reset_flag and reset_flag[0] == 'true':
                is_after_reset = True
                # Удаляем флаг после прочтения
                execute_query('UPDATE settings SET value = "false" WHERE key = "reset_occurred"')
        except:
            # Таблицы settings нет - игнорируем
            pass
    except:
        pass
    
    # Формируем приветствие
    if is_after_reset and bonus_given:
        welcome_text = (
            f"🔄 **ВНИМАНИЕ! ПЕРЕЗАГРУЗКА ВСЕЛЕННОЙ!** 🔄\n\n"
            f"👋 Привет, {user.first_name}!\n\n"
            f"🌌 Крипто-вселенная LEDOGE прошла хард-форк и обновилась!\n\n"
            f"🎁 **ТЫ ПОЛУЧИЛ:**\n"
            f"✅ 1000 LEDOGE (стартовый бонус)\n"
            f"✅ Все данные синхронизированы\n\n"
            f"💰 Твой баланс: {new_balance:.2f} LEDOGE\n\n"
            f"🚀 Начинай майнить прямо сейчас!"
        )
    elif bonus_given:
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"🎁 **СТАРТОВЫЙ БОНУС:** 1000 LEDOGE\n\n"
            f"💰 Твой баланс: {new_balance:.2f} LEDOGE\n\n"
            f"Добро пожаловать в <b>CryptoSim</b> — симулятор криптоэкономики.\n\n"
            f"🔹 <b>Что ты можешь делать:</b>\n"
            f"• ⛏ Майнить криптовалюту\n"
            f"• ☝ Тапать мем-коины\n"
            f"• ⚙️ Покупать майнеров\n"
            f"• 💱 Торговать на P2P бирже\n"
            f"• 🎰 Крутить колесо фортуны\n"
            f"• 👕 Покупать скины\n"
            f"• 💱 Обменивать валюту\n"
            f"• 🤝 Приглашать друзей\n"
            f"• 📈 Следить за курсами\n"
            f"• 📚 Изучать блокчейн"
        )
    else:
        welcome_text = (
            f"👋 С возвращением, {user.first_name}!\n\n"
            f"💰 Твой баланс: {new_balance:.2f} LEDOGE"
        )
    
    # Проверяем реферальный параметр
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        try:
            referrer_id = int(args[1].replace('ref_', ''))
            if referrer_id != user_id and referrer_id > 0:
                from handlers.referral import process_referral
                await process_referral(user_id, referrer_id)
        except:
            pass
    
    menu = await get_menu_for_user(user_id)
    await message.answer(welcome_text, reply_markup=menu)
    
    # Проверяем реферальный параметр
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        try:
            referrer_id = int(args[1].replace('ref_', ''))
            if referrer_id != user_id and referrer_id > 0:
                from handlers.referral import process_referral
                await process_referral(user_id, referrer_id)
        except:
            pass
    
    menu = await get_menu_for_user(user_id)
    await message.answer(welcome_text, reply_markup=menu)
