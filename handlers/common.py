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
    
    logger.info(f"👤 /start от пользователя {user_id}")
    
    # Получаем или создаем пользователя
    user_data = get_user(user_id, user.username, user.first_name)
    
    # Получаем баланс
    old_balance = get_balance(user_id, 'ledoge')
    
    # Начисляем бонус если надо
    bonus_given = False
    if old_balance == 0:
        update_balance(user_id, 'ledoge', 1000, 'add')
        new_balance = get_balance(user_id, 'ledoge')
        bonus_given = True
    else:
        new_balance = old_balance
    
    # Проверяем флаг перезагрузки
    is_after_reset = False
    try:
        conn = sqlite3.connect('/data/crypto_sim.db')
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if cur.fetchone():
            cur.execute('SELECT value FROM settings WHERE key = "reset_occurred"')
            reset_flag = cur.fetchone()
            if reset_flag and reset_flag[0] == 'true':
                is_after_reset = True
                cur.execute('UPDATE settings SET value = "false" WHERE key = "reset_occurred"')
                conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при проверке флага: {e}")
    
    # Формируем приветствие
    if is_after_reset and bonus_given:
        welcome_text = (
            f"🔄 **ПЕРЕЗАГРУЗКА ВСЕЛЕННОЙ!** 🔄\n\n"
            f"👋 Привет, {user.first_name}!\n\n"
            f"🌌 Крипто-вселенная LEDOGE обновилась!\n\n"
            f"🎁 **ТЫ ПОЛУЧИЛ:**\n"
            f"✅ 1000 LEDOGE\n"
            f"💰 Твой баланс: {new_balance:.2f} LEDOGE\n\n"
            f"🚀 Начинай майнить!"
        )
    elif bonus_given:
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"🎁 **СТАРТОВЫЙ БОНУС:** 1000 LEDOGE\n\n"
            f"💰 Твой баланс: {new_balance:.2f} LEDOGE\n\n"
            f"Добро пожаловать в CryptoSim!"
        )
    else:
        welcome_text = (
            f"👋 С возвращением, {user.first_name}!\n\n"
            f"💰 Твой баланс: {new_balance:.2f} LEDOGE"
        )
    
    # Получаем меню
    menu = await get_menu_for_user(user_id)
    
    # ОТПРАВЛЯЕМ ТОЛЬКО ОДНО СООБЩЕНИЕ!
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
