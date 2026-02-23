# handlers/shop.py
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import (
    get_user, get_balance, update_balance,
    get_user_skin, spin_wheel,
    calculate_gas
)
from keyboards import exchange_p2p_menu, main_menu
from config import CURRENCIES, ADMIN_ID, CURRENCY_PRICES, GAS_FEES

logger = logging.getLogger(__name__)

router = Router()

class ShopStates(StatesGroup):
    waiting_sell_order = State()
    waiting_transfer = State()
    waiting_buy_amount = State()

# Хранилище ордеров
orders = []
order_counter = 1

# ==================== P2P БИРЖА ====================

@router.message(F.text == "🏪 P2P Биржа")
async def show_exchange(message: Message):
    """Показывает главное меню P2P биржи"""
    await message.answer(
        "🏪 <b>P2P БИРЖА</b>\n\n"
        "Здесь можно продавать и покупать монеты напрямую у других игроков.\n\n"
        "💵 <b>Важно:</b> Все сделки только в USDToken!\n"
        "⛽ За каждую сделку взимается комиссия (газ):\n"
        f"• Продажа: {GAS_FEES['sell']*100}%\n"
        f"• Покупка: {GAS_FEES['buy']*100}%\n"
        f"• Перевод: {GAS_FEES['transfer']*100}%\n\n"
        "Выбери действие:",
        reply_markup=exchange_p2p_menu()
    )

@router.message(F.text == "💰 Продать монету")
async def sell_coin_start(message: Message, state: FSMContext):
    """Начало создания ордера на продажу"""
    text = (
        "💰 <b>ПРОДАЖА МОНЕТ</b>\n\n"
        "Напиши в формате: <code>валюта количество цена</code>\n"
        "Цена в USDToken за 1 единицу.\n\n"
        "Пример: <code>ledoge 100 5</code> (продать 100 LEDOGE по 5 USDToken)\n\n"
        "Доступные валюты:\n"
        "• ledoge - 🐶 LEDOGE\n"
        "• bitkoin - 🪙 BitKoin\n"
        "• ethireum - ⚡ Ethireum\n"
        "• dodgecoin - 🐕 DodgeCoin\n"
        "• tonkoin - 💎 TonKoin\n"
        "• solanafast - 🌲 SolanaFast\n"
        "• notcoine - 📱 NotCoine\n"
        "• shibafloki - 🐶 ShibaFloki\n\n"
        f"⛽ Комиссия при продаже: {GAS_FEES['sell']*100}% (удерживается с продавца)"
    )
    
    await message.answer(text)
    await state.set_state(ShopStates.waiting_sell_order)

@router.message(StateFilter(ShopStates.waiting_sell_order))
async def process_sell_order(message: Message, state: FSMContext):
    """Обрабатывает создание ордера на продажу"""
    global order_counter
    
    try:
        parts = message.text.lower().split()
        if len(parts) != 3:
            await message.answer("❌ Неправильный формат. Используй: валюта количество цена")
            await state.clear()
            return
        
        currency = parts[0]
        amount = float(parts[1])
        price = float(parts[2])
        
        if currency not in CURRENCIES:
            await message.answer(f"❌ Валюта {currency} не найдена")
            await state.clear()
            return
        
        user_id = message.from_user.id
        balance = get_balance(user_id, currency)
        
        if balance < amount:
            await message.answer(f"❌ У тебя только {balance} {currency}")
            await state.clear()
            return
        
        # Рассчитываем комиссию за продажу
        total_value = amount * price
        gas = calculate_gas(total_value, 'sell')
        
        order = {
            'id': order_counter,
            'seller_id': user_id,
            'seller_name': message.from_user.first_name,
            'currency': currency,
            'amount': amount,
            'price': price,
            'total': total_value,
            'gas': gas,
            'status': 'active'
        }
        orders.append(order)
        order_counter += 1
        
        await message.answer(
            f"✅ <b>ОРДЕР СОЗДАН!</b>\n\n"
            f"🆔 Номер: #{order['id']}\n"
            f"💱 Продажа: {amount} {CURRENCIES[currency]}\n"
            f"💰 Цена: {price} USDToken\n"
            f"💵 Всего: {total_value:.2f} USDToken\n"
            f"⛽ Комиссия при продаже: {gas:.4f} USDToken\n\n"
            f"<i>Купить: /buy {order['id']}</i>"
        )
        
    except ValueError:
        await message.answer("❌ Ошибка в числах. Используй формат: валюта количество цена")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

@router.message(F.text == "🛒 Купить монету")
async def show_orders(message: Message):
    """Показывает активные ордера на продажу"""
    if not orders:
        await message.answer("📭 Нет активных предложений")
        return
    
    # Фильтруем только активные ордера
    active_orders = [o for o in orders if o.get('status') == 'active']
    
    if not active_orders:
        await message.answer("📭 Нет активных предложений")
        return
    
    text = "🛒 <b>АКТИВНЫЕ ПРЕДЛОЖЕНИЯ</b>\n\n"
    
    for order in active_orders[-10:]:  # Показываем последние 10
        text += f"🆔 <b>#{order['id']}</b>\n"
        text += f"💱 {order['amount']} {CURRENCIES[order['currency']]}\n"
        text += f"💰 Цена: {order['price']} USDToken\n"
        text += f"💵 Всего: {order['total']:.2f} USDToken\n"
        text += f"👤 Продавец: {order['seller_name']}\n"
        text += f"⛽ Комиссия при покупке: {calculate_gas(order['total'], 'buy'):.4f} USDToken\n"
        text += "──────────────\n\n"
    
    text += "<i>Чтобы купить, напиши:</i> /buy НОМЕР"
    
    await message.answer(text)

@router.message(F.text.startswith("/buy"))
async def buy_order(message: Message):
    """Покупает монеты по ордеру"""
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("❌ Используй: /buy номер")
            return
        
        order_id = int(parts[1])
        
        # Ищем ордер
        order = None
        for o in orders:
            if o['id'] == order_id and o.get('status') == 'active':
                order = o
                break
        
        if not order:
            await message.answer("❌ Ордер не найден или уже куплен")
            return
        
        buyer_id = message.from_user.id
        buyer_name = message.from_user.first_name
        
        # Нельзя купить у самого себя
        if buyer_id == order['seller_id']:
            await message.answer("❌ Нельзя купить у самого себя")
            return
        
        # Проверяем баланс покупателя (USDToken)
        buyer_usdt = get_balance(buyer_id, 'usdtoken')
        need_usdt = order['total']
        
        # Рассчитываем комиссию за покупку
        gas = calculate_gas(need_usdt, 'buy')
        total_with_gas = need_usdt + gas
        
        if buyer_usdt < total_with_gas:
            await message.answer(
                f"❌ Недостаточно USDToken\n"
                f"Цена: {need_usdt:.2f} USDToken\n"
                f"Газ: {gas:.4f} USDToken\n"
                f"Всего нужно: {total_with_gas:.4f} USDToken\n"
                f"У тебя: {buyer_usdt:.4f} USDToken"
            )
            return
        
        # Совершаем сделку
        # Списываем USDToken + газ у покупателя
        update_balance(buyer_id, 'usdtoken', total_with_gas, 'subtract')
        # Начисляем валюту покупателю
        update_balance(buyer_id, order['currency'], order['amount'], 'add')
        
        # Начисляем продавцу USDToken (без газа)
        seller_payout = need_usdt
        update_balance(order['seller_id'], 'usdtoken', seller_payout, 'add')
        # Списываем валюту у продавца
        update_balance(order['seller_id'], order['currency'], order['amount'], 'subtract')
        
        # Помечаем ордер как выполненный
        order['status'] = 'sold'
        
        # Уведомление продавцу
        try:
            await message.bot.send_message(
                order['seller_id'],
                f"💰 <b>ТВОЙ ОРДЕР #{order['id']} КУПЛЕН!</b>\n\n"
                f"👤 Покупатель: {buyer_name}\n"
                f"💱 Продано: {order['amount']} {CURRENCIES[order['currency']]}\n"
                f"💵 Получено: {seller_payout:.2f} USDToken\n"
                f"⛽ Комиссия продавца: {order['gas']:.4f} USDToken (удержана при создании)"
            )
        except:
            pass  # Игрок не в сети или заблокировал бота
        
        # Сообщение покупателю
        await message.answer(
            f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
            f"🆔 Ордер #{order['id']}\n"
            f"💱 Куплено: {order['amount']} {CURRENCIES[order['currency']]}\n"
            f"💵 Цена: {need_usdt:.2f} USDToken\n"
            f"⛽ Газ (покупателя): {gas:.4f} USDToken\n"
            f"💰 Итого списано: {total_with_gas:.4f} USDToken"
        )
        
    except ValueError:
        await message.answer("❌ Номер должен быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка при покупке: {e}")

@router.message(F.text == "🎁 Перевести другу")
async def transfer_start(message: Message, state: FSMContext):
    """Начинает процесс перевода монет другу"""
    await message.answer(
        "🎁 <b>ПЕРЕВОД ДРУГУ</b>\n\n"
        "Формат: <code>@username валюта количество</code>\n"
        "Пример: <code>@durov ledoge 100</code>\n\n"
        f"⛽ Комиссия за перевод: {GAS_FEES['transfer']*100}%\n\n"
        "Доступные валюты: ledoge, bitkoin, notcoine, shibafloki, tonkoin, solanafast, ethireum"
    )
    await state.set_state(ShopStates.waiting_transfer)

@router.message(StateFilter(ShopStates.waiting_transfer))
async def process_transfer(message: Message, state: FSMContext):
    """Обрабатывает перевод монет"""
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Неправильный формат. Используй: @username валюта количество")
            await state.clear()
            return
        
        username = parts[0].replace('@', '')
        currency = parts[1].lower()
        amount = float(parts[2])
        
        if currency not in CURRENCIES:
            await message.answer(f"❌ Валюта {currency} не найдена")
            await state.clear()
            return
        
        sender_id = message.from_user.id
        sender_name = message.from_user.first_name
        balance = get_balance(sender_id, currency)
        
        if balance < amount:
            await message.answer(f"❌ У тебя только {balance} {currency}")
            await state.clear()
            return
        
        # Рассчитываем комиссию за перевод
        gas = calculate_gas(amount, 'transfer')
        total_with_gas = amount + gas
        
        if balance < total_with_gas:
            await message.answer(
                f"❌ Недостаточно средств с учётом комиссии\n"
                f"Сумма: {amount} {currency}\n"
                f"Газ: {gas:.4f} {currency}\n"
                f"Всего нужно: {total_with_gas:.4f} {currency}\n"
                f"У тебя: {balance:.4f} {currency}"
            )
            await state.clear()
            return
        
        # TODO: Здесь нужно найти user_id по username
        # Пока просто информационное сообщение
        
        # Списываем сумму + комиссию
        update_balance(sender_id, currency, total_with_gas, 'subtract')
        
        await message.answer(
            f"✅ <b>ПЕРЕВОД ОТПРАВЛЕН!</b>\n\n"
            f"👤 Получатель: @{username}\n"
            f"💱 Отправлено: {amount} {CURRENCIES[currency]}\n"
            f"⛽ Комиссия: {gas:.4f} {currency}\n"
            f"💰 Итого списано: {total_with_gas:.4f} {currency}\n\n"
            f"<i>В демо-версии монеты не зачисляются автоматически.</i>"
        )
        
    except ValueError:
        await message.answer("❌ Ошибка в числах")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

# ==================== КОЛЕСО ФОРТУНЫ ====================

@router.message(F.text == "🎰 Колесо фортуны")
async def show_wheel(message: Message):
    """Показывает колесо фортуны"""
    user_id = message.from_user.id
    balance = get_balance(user_id, 'ledoge')
    
    await message.answer(
        f"🎰 <b>КОЛЕСО ФОРТУНЫ</b>\n\n"
        f"Испытай удачу! Крутить стоит 10 LEDOGE.\n"
        f"Шансы:\n"
        f"• 1% — ДЖЕКПОТ x10\n"
        f"• 9% — x3\n"
        f"• 30% — x1.5\n"
        f"• 60% — проигрыш\n\n"
        f"💰 Твой баланс: {balance:.2f} LEDOGE\n\n"
        f"<i>В реальности такие игры — высокорисковые инвестиции!</i>",
        reply_markup=wheel_keyboard()
    )

@router.callback_query(F.data == "wheel_spin")
async def process_wheel_spin(callback: CallbackQuery):
    """Обрабатывает вращение колеса фортуны"""
    user_id = callback.from_user.id
    
    success, result_message, win_amount = spin_wheel(user_id, 'ledoge', 10)
    
    if not success:
        await callback.answer("❌ " + result_message, show_alert=True)
        return
    
    new_balance = get_balance(user_id, 'ledoge')
    
    await callback.message.edit_text(
        f"🎰 <b>РЕЗУЛЬТАТ:</b>\n\n"
        f"{result_message}\n\n"
        f"💰 Новый баланс: {new_balance:.2f} LEDOGE",
        reply_markup=wheel_keyboard()
    )
    
    await callback.answer()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def wheel_keyboard():
    """Клавиатура для колеса фортуны"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = [
        [InlineKeyboardButton(text="🎲 Крутить за 10 LEDOGE", callback_data="wheel_spin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== НАЗАД ====================

@router.message(F.text == "◀ Назад в меню")
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        from keyboards import admin_keyboard
        await message.answer("🔧 Админ-меню:", reply_markup=admin_keyboard())
    else:
        await message.answer("Главное меню:", reply_markup=main_menu())