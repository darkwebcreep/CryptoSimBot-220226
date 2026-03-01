# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sqlite3
import json
from database import update_balance, get_balance
from config import ADMIN_ID, CURRENCIES
from keyboards import admin_keyboard

router = Router()

class AdminStates(StatesGroup):
    waiting_coin_give = State()
    waiting_broadcast = State()

async def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not await is_admin(message):
        await message.answer("⛔ Доступ запрещен")
        return
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_keyboard()
    )

@router.message(F.text == "🔧 Выдать монеты")
async def give_coins_start(message: Message, state: FSMContext):
    if not await is_admin(message):
        return
    
    await message.answer(
        "💰 <b>Выдача монет</b>\n\n"
        "Напиши в формате: <code>user_id валюта количество</code>\n"
        "Пример: <code>123456789 ledoge 1000</code>\n\n"
        "Доступные валюты: " + ", ".join(CURRENCIES.keys())
    )
    await state.set_state(AdminStates.waiting_coin_give)

@router.message(StateFilter(AdminStates.waiting_coin_give))
async def process_give_coins(message: Message, state: FSMContext):
    if not await is_admin(message):
        await state.clear()
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Неправильный формат. Используй: user_id валюта количество")
            await state.clear()
            return
        
        target_id = int(parts[0])
        currency = parts[1].lower()
        amount = float(parts[2])
        
        if currency not in CURRENCIES:
            await message.answer(f"❌ Валюта {currency} не найдена")
            await state.clear()
            return
        
        success = update_balance(target_id, currency, amount, 'add')
        
        if success:
            await message.answer(
                f"✅ <b>Выдано!</b>\n\n"
                f"Пользователь: {target_id}\n"
                f"Валюта: {CURRENCIES[currency]}\n"
                f"Количество: {amount}\n"
                f"💰 Новый баланс: {get_balance(target_id, currency)}"
            )
        else:
            await message.answer("❌ Ошибка при выдаче монет")
        
    except ValueError:
        await message.answer("❌ Ошибка в числах")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

@router.message(F.text == "📢 Сделать рассылку")
async def broadcast_start(message: Message, state: FSMContext):
    if not await is_admin(message):
        return
    
    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "Напиши текст для рассылки всем пользователям.\n"
        "Можно использовать HTML-теги: <b>жирный</b>, <i>курсив</i>"
    )
    await state.set_state(AdminStates.waiting_broadcast)

@router.message(StateFilter(AdminStates.waiting_broadcast))
async def process_broadcast(message: Message, state: FSMContext):
    if not await is_admin(message):
        await state.clear()
        return
    
    broadcast_text = message.text
    
    conn = sqlite3.connect('crypto_sim.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users')
    users = cur.fetchall()
    conn.close()
    
    status_msg = await message.answer(
        f"📤 Начинаю рассылку...\n"
        f"Всего получателей: {len(users)}"
    )
    
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Всего пользователей: {len(users)}\n"
        f"Текст: {broadcast_text[:100]}..." + ("..." if len(broadcast_text) > 100 else "")
    )
    
    await state.clear()

@router.message(F.text == "📊 Статистика бота")
async def bot_stats(message: Message):
    if not await is_admin(message):
        return
    
    conn = sqlite3.connect('crypto_sim.db')
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM users')
    total_users = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM users WHERE wheel_spins > 0')
    active_users = cur.fetchone()[0]
    
    cur.execute('SELECT SUM(wheel_spins) FROM users')
    total_spins = cur.fetchone()[0] or 0
    
    cur.execute('SELECT SUM(wheel_wins) FROM users')
    total_wins = cur.fetchone()[0] or 0
    
    cur.execute('SELECT skin, COUNT(*) FROM users WHERE skin != "none" GROUP BY skin')
    skin_stats = cur.fetchall()
    
    conn.close()
    
    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🎲 Игроков (крутили колесо): {active_users}\n"
        f"🔄 Всего спинов: {total_spins}\n"
        f"🏆 Всего выигрышей: {total_wins}\n"
    )
    
    if total_spins > 0:
        text += f"📈 Процент побед: {total_wins/total_spins*100:.1f}%\n"
    
    if skin_stats:
        text += "\n👕 <b>Скины:</b>\n"
        for skin, count in skin_stats:
            from config import SKINS
            skin_name = SKINS.get(skin, {}).get('name', skin)
            text += f"  {skin_name}: {count} чел.\n"
    
    await message.answer(text)

@router.message(F.text == "👤 Режим пользователя")
async def switch_to_user_mode(message: Message):
    if not await is_admin(message):
        return
    
    from keyboards import main_menu
    await message.answer(
        "👤 <b>Режим обычного пользователя</b>\n\n"
        "Теперь ты видишь меню как обычный игрок.\n"
        "Чтобы вернуться в админку, напиши /admin",
        reply_markup=main_menu()
    )

@router.message(F.text == "👑 Особый скин")
async def give_dev_skin(message: Message):
    if not await is_admin(message):
        return
    
    user_id = message.from_user.id
    
    conn = sqlite3.connect('crypto_sim.db')
    cur = conn.cursor()
    cur.execute('UPDATE users SET skin = ? WHERE user_id = ?', ('developer', user_id))
    conn.commit()
    conn.close()
    
    await message.answer(
        "👑 <b>Особый скин активирован!</b>\n\n"
        "Теперь в топе ты будешь отображаться с особенным пёсиком! 🐕‍🦺"
    )

# ========== НОВАЯ ФУНКЦИЯ ДЛЯ ПЕРЕЗАГРУЗКИ ==========
@router.message(F.text == "🔄 Перезагрузка")
async def announce_reset(message: Message):
    """Объявляет о перезагрузке вселенной и раздает бонусы"""
    if not await is_admin(message):
        return
    
    await message.answer("🔄 Начинаю процедуру перезагрузки вселенной...")
    
    try:
        import sqlite3
        import json
        
        conn = sqlite3.connect('/data/crypto_sim.db')
        cur = conn.cursor()
        
        # Создаем таблицу настроек, если её нет
        cur.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Устанавливаем флаг перезагрузки
        cur.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', ('reset_occurred', 'true'))
        
        # Получаем всех пользователей
        cur.execute('SELECT user_id FROM users')
        users = cur.fetchall()
        
        bonus_count = 0
        for user in users:
            user_id = user[0]
            
            # Получаем текущий баланс
            cur.execute('SELECT balances FROM balances WHERE user_id = ?', (user_id,))
            result = cur.fetchone()
            
            if result and result[0]:
                balances = json.loads(result[0])
            else:
                balances = {}
            
            # Добавляем 1000 LEDOGE
            balances['ledoge'] = balances.get('ledoge', 0) + 1000
            bonus_count += 1
            
            # Сохраняем
            cur.execute('UPDATE balances SET balances = ? WHERE user_id = ?', 
                       (json.dumps(balances), user_id))
        
        conn.commit()
        conn.close()
        
        await message.answer(
            f"✅ **ПЕРЕЗАГРУЗКА ЗАВЕРШЕНА!**\n\n"
            f"📢 Объявление о перезагрузке будет показано всем игрокам при следующем входе.\n"
            f"💰 Бонус 1000 LEDOGE начислен {bonus_count} пользователям!"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ========== КОНЕЦ НОВОЙ ФУНКЦИИ ==========
