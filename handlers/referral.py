# handlers/referral.py
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import get_connection, update_balance
from config import REFERRAL_SETTINGS, ADMIN_ID
import sqlite3

logger = logging.getLogger(__name__)

router = Router()

def generate_referral_link(bot_username: str, user_id: int) -> str:
    """Генерирует реферальную ссылку"""
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

async def process_referral(new_user_id: int, referrer_id: int):
    """Обрабатывает реферала"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Проверяем существование таблицы referrals
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if not cur.fetchone():
        # Создаём таблицу, если её нет
        cur.execute('''
            CREATE TABLE referrals (
                referrer_id INTEGER,
                referral_id INTEGER,
                referral_date TEXT,
                total_earned REAL DEFAULT 0,
                PRIMARY KEY (referrer_id, referral_id)
            )
        ''')
        conn.commit()
    
    cur.execute('SELECT * FROM referrals WHERE referral_id = ?', (new_user_id,))
    if cur.fetchone():
        conn.close()
        return False
    
    cur.execute('''
        INSERT INTO referrals (referrer_id, referral_id, referral_date, total_earned)
        VALUES (?, ?, ?, 0)
    ''', (referrer_id, new_user_id, datetime.now().isoformat()))
    
    # Проверяем существование колонки referrer_id в users
    try:
        cur.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, new_user_id))
    except sqlite3.OperationalError:
        # Если колонки нет, добавляем её
        cur.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0")
        cur.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, new_user_id))
    
    bonus = REFERRAL_SETTINGS['reward_for_invite']
    update_balance(referrer_id, 'ledoge', bonus, 'add')
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Новый реферал! {referrer_id} пригласил {new_user_id}, бонус {bonus} LEDOGE")
    return True

async def add_referral_income(referrer_id: int, amount: float, currency: str):
    """Начисляет доход рефереру от активности реферала"""
    if amount < REFERRAL_SETTINGS['min_payout']:
        return
    
    bonus = amount * REFERRAL_SETTINGS['reward_percent_permanent']
    
    if bonus > 0:
        update_balance(referrer_id, currency, bonus, 'add')
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Проверяем существование таблицы referrals
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
        if cur.fetchone():
            cur.execute('''
                UPDATE referrals 
                SET total_earned = total_earned + ? 
                WHERE referrer_id = ?
            ''', (bonus, referrer_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💰 Реферальный бонус: {referrer_id} получил {bonus} {currency}")

@router.message(F.text == "🤝 Рефералы")
async def show_referral_info(message: Message, state: FSMContext):
    """Показывает реферальную информацию"""
    # Очищаем состояние, если оно было
    await state.clear()
    
    user_id = message.from_user.id
    bot = await message.bot.get_me()
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Проверяем и создаём таблицы при необходимости
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if not cur.fetchone():
        cur.execute('''
            CREATE TABLE referrals (
                referrer_id INTEGER,
                referral_id INTEGER,
                referral_date TEXT,
                total_earned REAL DEFAULT 0,
                PRIMARY KEY (referrer_id, referral_id)
            )
        ''')
        conn.commit()
    
    # Получаем статистику рефералов
    cur.execute('SELECT COUNT(*), SUM(total_earned) FROM referrals WHERE referrer_id = ?', (user_id,))
    result = cur.fetchone()
    referrals_count = result[0] or 0
    total_earned = result[1] or 0
    
    # Получаем информацию о том, кто пригласил пользователя
    try:
        cur.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
        referrer = cur.fetchone()
        referrer_id = referrer[0] if referrer else 0
    except sqlite3.OperationalError:
        # Если колонки нет, добавляем её
        try:
            cur.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0")
            conn.commit()
        except:
            pass
        referrer_id = 0
    
    conn.close()
    
    text = "🤝 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
    text += f"🔗 <b>Твоя ссылка:</b>\n"
    text += f"{generate_referral_link(bot.username, user_id)}\n\n"
    text += f"📊 <b>Твоя статистика:</b>\n"
    text += f"• Приглашено друзей: {referrals_count}\n"
    text += f"• Заработано с рефералов: {total_earned:.2f} LEDOGE\n\n"
    
    if referrer_id and referrer_id != 0:
        # Получаем имя пригласившего
        try:
            cur.execute('SELECT first_name, username FROM users WHERE user_id = ?', (referrer_id,))
            inviter = cur.fetchone()
            if inviter:
                inviter_name = inviter[0] or inviter[1] or f"ID {referrer_id}"
                text += f"👤 <b>Тебя пригласил:</b> {inviter_name}\n\n"
            else:
                text += f"👤 <b>Тебя пригласил:</b> ID {referrer_id}\n\n"
        except:
            text += f"👤 <b>Тебя пригласил:</b> ID {referrer_id}\n\n"
    
    text += f"🎁 <b>Бонусы:</b>\n"
    text += f"• {REFERRAL_SETTINGS['reward_for_invite']} LEDOGE за друга\n"
    text += f"• {REFERRAL_SETTINGS['reward_percent_permanent']*100}% от всего дохода друга\n\n"
    text += f"<i>Приглашай друзей и зарабатывай!</i>"
    
    kb = [
        [KeyboardButton(text="📊 Мои рефералы")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(text, reply_markup=markup)

@router.message(F.text == "📊 Мои рефералы")
async def show_my_referrals(message: Message, state: FSMContext):
    """Показывает список рефералов"""
    # Очищаем состояние, если оно было
    await state.clear()
    
    user_id = message.from_user.id
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Проверяем существование таблицы referrals
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if not cur.fetchone():
        await message.answer("📭 У тебя пока нет рефералов. Приглашай друзей!")
        conn.close()
        return
    
    cur.execute('''
        SELECT r.referral_id, u.first_name, u.username, r.referral_date, r.total_earned
        FROM referrals r
        LEFT JOIN users u ON r.referral_id = u.user_id
        WHERE r.referrer_id = ?
        ORDER BY r.referral_date DESC
    ''', (user_id,))
    
    referrals = cur.fetchall()
    conn.close()
    
    if not referrals:
        await message.answer("📭 У тебя пока нет рефералов. Приглашай друзей!")
        return
    
    text = "📊 <b>ТВОИ РЕФЕРАЛЫ</b>\n\n"
    
    for i, (ref_id, name, username, date, earned) in enumerate(referrals, 1):
        name_display = name or username or f"User{ref_id}"
        try:
            date_obj = datetime.fromisoformat(date)
            date_str = date_obj.strftime("%d.%m.%Y")
        except:
            date_str = "неизвестно"
        
        text += f"{i}. {name_display}\n"
        text += f"   📅 {date_str}\n"
        text += f"   💰 Заработано: {earned:.2f} LEDOGE\n\n"
    
    await message.answer(text)

@router.message(Command("ref"))
async def cmd_ref(message: Message, state: FSMContext):
    """Альтернативная команда для рефералов"""
    await show_referral_info(message, state)

@router.message(F.text == "◀ Назад в меню")
async def back_to_main(message: Message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        from keyboards import admin_keyboard
        await message.answer("🔧 Админ-меню:", reply_markup=admin_keyboard())
    else:
        from keyboards import main_menu
        await message.answer("Главное меню:", reply_markup=main_menu())