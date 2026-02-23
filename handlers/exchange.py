# handlers/exchange.py
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_balance, update_balance
from keyboards import main_menu
from config import ADMIN_ID, CURRENCY_PRICES

logger = logging.getLogger(__name__)

router = Router()

class ExchangeStates(StatesGroup):
    waiting_ledoge_to_usdt = State()
    waiting_usdt_to_ledoge = State()

# Курс обмена (можно менять)
LEDOGE_TO_USDT = 10  # 10 LEDOGE = 1 USDT
USDT_TO_LEDOGE = 10  # 1 USDT = 10 LEDOGE

@router.message(F.text == "💱 Обменник")
async def show_exchange(message: Message):
    user_id = message.from_user.id
    ledoge = get_balance(user_id, 'ledoge')
    usdt = get_balance(user_id, 'usdtoken')
    
    text = "💱 <b>ОБМЕН ВАЛЮТ</b>\n\n"
    text += f"💰 Твои средства:\n"
    text += f"🐶 LEDOGE: {ledoge:.2f}\n"
    text += f"💵 USDToken: {usdt:.2f}\n\n"
    
    text += "📊 <b>Курсы валют (в USDToken):</b>\n"
    text += f"• 📱 NotCoine: {CURRENCY_PRICES['notcoine']} USDToken\n"
    text += f"• 🐶 ShibaFloki: {CURRENCY_PRICES['shibafloki']} USDToken\n"
    text += f"• 🌲 SolanaFast: {CURRENCY_PRICES['solanafast']} USDToken\n"
    text += f"• 💎 TonKoin: {CURRENCY_PRICES['tonkoin']} USDToken\n"
    text += f"• 🐕 DodgeCoin: {CURRENCY_PRICES['dodgecoin']} USDToken\n"
    text += f"• ⚡ Ethireum: {CURRENCY_PRICES['ethireum']} USDToken\n"
    text += f"• 🪙 BitKoin: {CURRENCY_PRICES['bitkoin']} USDToken\n"
    text += f"• 🐶 LEDOGE: {CURRENCY_PRICES['ledoge']} USDToken\n\n"
    
    text += "💱 <b>Доступные операции:</b>\n"
    text += "• LEDOGE → USDToken (10:1)\n"
    text += "• USDToken → LEDOGE (1:10)\n\n"
    text += "<i>P2P биржа работает только с USDToken!</i>"
    
    # Создаем клавиатуру
    kb = [
        [KeyboardButton(text="💵 LEDOGE → USDToken")],
        [KeyboardButton(text="🪙 USDToken → LEDOGE")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(text, reply_markup=markup)

@router.message(F.text == "💵 LEDOGE → USDToken")
async def ledoge_to_usdt_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    ledoge = get_balance(user_id, 'ledoge')
    
    if ledoge < LEDOGE_TO_USDT:
        await message.answer(
            f"❌ Для обмена нужно минимум {LEDOGE_TO_USDT} LEDOGE.\n"
            f"У тебя: {ledoge:.2f} LEDOGE"
        )
        return
    
    await message.answer(
        f"💵 <b>Обмен LEDOGE → USDToken</b>\n\n"
        f"Курс: {LEDOGE_TO_USDT} LEDOGE = 1 USDToken\n"
        f"У тебя: {ledoge:.2f} LEDOGE\n\n"
        f"Сколько USDToken хочешь купить?\n"
        f"(Напиши число от 1 до {int(ledoge // LEDOGE_TO_USDT)})"
    )
    await state.set_state(ExchangeStates.waiting_ledoge_to_usdt)

@router.message(ExchangeStates.waiting_ledoge_to_usdt)
async def process_ledoge_to_usdt(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    try:
        usdt_amount = int(message.text)
        if usdt_amount <= 0:
            await message.answer("❌ Число должно быть больше 0")
            await state.clear()
            return
        
        need_ledoge = usdt_amount * LEDOGE_TO_USDT
        ledoge_balance = get_balance(user_id, 'ledoge')
        
        if ledoge_balance < need_ledoge:
            await message.answer(
                f"❌ Недостаточно LEDOGE!\n"
                f"Нужно: {need_ledoge} LEDOGE\n"
                f"У тебя: {ledoge_balance:.2f} LEDOGE"
            )
            await state.clear()
            return
        
        # Проводим обмен
        update_balance(user_id, 'ledoge', need_ledoge, 'subtract')
        update_balance(user_id, 'usdtoken', usdt_amount, 'add')
        
        new_ledoge = get_balance(user_id, 'ledoge')
        new_usdt = get_balance(user_id, 'usdtoken')
        
        await message.answer(
            f"✅ <b>Обмен выполнен!</b>\n\n"
            f"💰 Потрачено: {need_ledoge} LEDOGE\n"
            f"💵 Получено: {usdt_amount} USDToken\n\n"
            f"📊 Новый баланс:\n"
            f"🐶 LEDOGE: {new_ledoge:.2f}\n"
            f"💵 USDToken: {new_usdt:.2f}"
        )
        
    except ValueError:
        await message.answer("❌ Введи целое число")
    finally:
        await state.clear()

@router.message(F.text == "🪙 USDToken → LEDOGE")
async def usdt_to_ledoge_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    usdt = get_balance(user_id, 'usdtoken')
    
    if usdt < 1:
        await message.answer(
            f"❌ Для обмена нужно минимум 1 USDToken.\n"
            f"У тебя: {usdt:.2f} USDToken"
        )
        return
    
    await message.answer(
        f"🪙 <b>Обмен USDToken → LEDOGE</b>\n\n"
        f"Курс: 1 USDToken = {USDT_TO_LEDOGE} LEDOGE\n"
        f"У тебя: {usdt:.2f} USDToken\n\n"
        f"Сколько USDToken хочешь обменять?\n"
        f"(Напиши число от 1 до {int(usdt)})"
    )
    await state.set_state(ExchangeStates.waiting_usdt_to_ledoge)

@router.message(ExchangeStates.waiting_usdt_to_ledoge)
async def process_usdt_to_ledoge(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    try:
        usdt_amount = int(message.text)
        if usdt_amount <= 0:
            await message.answer("❌ Число должно быть больше 0")
            await state.clear()
            return
        
        usdt_balance = get_balance(user_id, 'usdtoken')
        
        if usdt_balance < usdt_amount:
            await message.answer(
                f"❌ Недостаточно USDToken!\n"
                f"Нужно: {usdt_amount} USDToken\n"
                f"У тебя: {usdt_balance:.2f} USDToken"
            )
            await state.clear()
            return
        
        # Проводим обмен
        get_ledoge = usdt_amount * USDT_TO_LEDOGE
        update_balance(user_id, 'usdtoken', usdt_amount, 'subtract')
        update_balance(user_id, 'ledoge', get_ledoge, 'add')
        
        new_ledoge = get_balance(user_id, 'ledoge')
        new_usdt = get_balance(user_id, 'usdtoken')
        
        await message.answer(
            f"✅ <b>Обмен выполнен!</b>\n\n"
            f"💵 Потрачено: {usdt_amount} USDToken\n"
            f"🐶 Получено: {get_ledoge} LEDOGE\n\n"
            f"📊 Новый баланс:\n"
            f"🐶 LEDOGE: {new_ledoge:.2f}\n"
            f"💵 USDToken: {new_usdt:.2f}"
        )
        
    except ValueError:
        await message.answer("❌ Введи целое число")
    finally:
        await state.clear()

# Назад в меню
@router.message(F.text == "◀ Назад в меню")
async def back_to_main(message: Message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        from keyboards import admin_keyboard
        await message.answer("🔧 Админ-меню:", reply_markup=admin_keyboard())
    else:
        await message.answer("Главное меню:", reply_markup=main_menu())