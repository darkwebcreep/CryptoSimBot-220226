# handlers/common.py
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime

from database import get_user, get_balance, get_user_skin, get_top_users, get_user_miners, get_user_owned_skins
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

# handlers/common.py (только функция cmd_start)

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    user_id = user.id
    
    # Middleware уже создал пользователя, просто логируем
    logger.info(f"👤 /start от пользователя {user_id} (@{user.username})")
    
    # Проверяем реферальный параметр
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        try:
            referrer_id = int(args[1].replace('ref_', ''))
            if referrer_id != user_id:
                from handlers.referral import process_referral
                await process_referral(user_id, referrer_id)
        except:
            pass
    
    menu = await get_menu_for_user(user_id)
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
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
        f"• 📚 Изучать блокчейн\n\n"
        f"Используй кнопки ниже 👇"
    )
    
    await message.answer(welcome_text, reply_markup=menu)
    
@router.message(F.text == "💰 Криптокошелёк")
async def show_wallet(message: Message):
    user_id = message.from_user.id
    
    # Собираем балансы в словарь с названиями
    balances = {}
    for code, name in CURRENCIES.items():
        balances[name] = get_balance(user_id, code)
    
    miners = get_user_miners(user_id)
    owned_skins = get_user_owned_skins(user_id)
    current_skin = get_user_skin(user_id)
    
    text = create_wallet_info(balances, miners, MINERS, owned_skins, SKINS, current_skin)
    
    await message.answer(text)

@router.message(F.text == "📊 Топ майнеров")
async def show_top(message: Message):
    top_users = get_top_users(15)
    
    if not top_users:
        await message.answer("📭 Пока нет игроков в топе")
        return
    
    text = create_top_list(top_users, SKINS)
    
    await message.answer(text)

@router.message(F.text == "ℹ Обучение")
async def show_education(message: Message):
    text = (
        create_header("КРИПТО-ЭНЦИКЛОПЕДИЯ", "📚") + "\n\n"
        
        "🔹 <b>Что такое блокчейн?</b>\n"
        "Блокчейн — это цифровая цепочка блоков, где каждый блок содержит информацию о транзакциях. "
        "Она хранится одновременно на тысячах компьютеров, поэтому её нельзя подделать или взломать.\n\n"
        
        "🔹 <b>Как работает майнинг?</b>\n"
        "Майнеры решают сложные математические задачи. Кто первый нашёл решение — получает награду (новые монеты). "
        "В нашей игре ты можешь купить майнеры, которые увеличат твой шанс на успех!\n\n"
        
        "🔹 <b>Что такое газ (комиссия)?</b>\n"
        "В реальном блокчейне за каждую операцию нужно платить комиссию — это называется газ. "
        "В нашей игре мы тоже добавили комиссию на P2P рынке, чтобы сделать экономику реалистичнее.\n\n"
        
        "🔹 <b>Типы криптовалют:</b>\n"
        "• <b>Мем-коины</b> (LEDOGE, NotCoine, ShibaFloki) — созданы на основе мемов, очень волатильны\n"
        "• <b>Альткоины</b> (Ethireum, SolanaFast) — серьёзные проекты с технологиями\n"
        "• <b>Классика</b> (BitKoin) — первая и самая дорогая криптовалюта\n"
        "• <b>Стейблкоины</b> (USDToken) — привязаны к доллару, не меняют цену\n\n"
        
        "🔹 <b>Как работает биржа?</b>\n"
        "1. Сначала ты покупаешь USDToken за LEDOGE в обменнике\n"
        "2. Потом можешь купить любую валюту на P2P бирже\n"
        "3. При каждой сделке взимается комиссия (газ)\n\n"
        
        "🔹 <b>Совет:</b> Покупай майнеры, они увеличивают шанс добычи редких монет!\n\n"
        
        "<i>Хочешь узнать больше? Читай мой канал @LEDOGEchannel!</i>"
    )
    await message.answer(text)

@router.message(F.text == "◀ Назад в меню")
async def back_to_menu(message: Message):
    user_id = message.from_user.id
    
    menu = await get_menu_for_user(user_id)
    
    if user_id == ADMIN_ID:
        await message.answer("🔧 Главное меню (режим администратора):", reply_markup=menu)
    else:
        await message.answer("Главное меню:", reply_markup=menu)
