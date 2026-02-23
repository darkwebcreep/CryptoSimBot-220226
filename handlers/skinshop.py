# handlers/skinshop.py
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_balance, get_user_skin, get_user_owned_skins,
    buy_skin, equip_skin, remove_skin
)
from keyboards import main_menu, shop_menu, wardrobe_menu, yes_no_menu
from config import SKINS, ADMIN_ID

logger = logging.getLogger(__name__)

router = Router()

class SkinShopStates(StatesGroup):
    waiting_skin_number = State()
    waiting_buy_confirm = State()
    waiting_wardrobe_number = State()
    waiting_equip_confirm = State()

# Словарь для временного хранения выбранного скина
temp_skin_choice = {}

# Полный список скинов с номерами
ALL_SKINS = [
    (1, 'bronze', 'Бронзовая кость', 500, 'ledoge', '🥉', 'Простая кость для простых людей'),
    (2, 'silver', 'Серебряный бульдог', 2000, 'ledoge', '🥈', 'Серебро всегда в цене'),
    (3, 'gold', 'Золотой бульдог', 5000, 'ledoge', '🥇', 'Король крипты!'),
    (4, 'diamond', 'Бриллиантовый бульдог', 10000, 'ledoge', '💎', 'Бриллиантовая ручка'),
    (5, 'satoshi', 'Satoshi Nakamoto', 10, 'bitkoin', '👤', 'Никто не узнает кто ты'),
    (6, 'joseph', 'Джозеф', 50, 'ledoge', '🐺', 'Это будет замечательный день, замечательный...'),
    (7, 'enlightened', 'Просвещённый', 10, 'ledoge', '📖', 'Тяжело в учении - легко в бою!'),
    (8, 'bateman', 'Патрик Бейтман', 20, 'ledoge', '🪓', 'Я люблю свою работу. Она приносит мне кучу денег.'),
    (9, 'autoclicker', 'АвтоКликер', 1000, 'notcoine', '👆', 'Самый быстрый палец на диком западе'),
    (10, 'hachiko', 'Хатико', 10000, 'shibafloki', '😞', 'Я буду ждать торги...'),
    (11, 'heisenberg', 'Хайзенберг', 10, 'tonkoin', '👨‍🔬', 'Скажи моё имя'),
    (12, 'superpepper', 'Суперперец!', 5, 'tonkoin', '🌶️', 'Почему только это и Мухаммед?!'),
    (13, 'belfort', 'Джордан Белфорт', 500000, 'ledoge', '💵', '22 миллиона долларов за 3 грёбаных часа!'),
    (14, 'sonic', 'Соник', 1000000, 'notcoine', '🦔', 'Они зовут меня Соник'),
    (15, 'error404', '404', 2, 'solanafast', '🚫', 'ERROR'),
    (16, 'hamster', 'Хомяк', 10, 'notcoine', '🐹', 'Тап Тап Тап по хомяку'),
    (17, 'angrybird', 'Злая птичка', 1, 'solanafast', '🐦', 'Я играю в энгри бёрдс'),
    (18, 'greedy', 'Алчный', 100, 'ethireum', '🤑', 'Бабки, бабки песик, БАБКИ!'),
    (19, 'star', 'Звёздный игрок!', 12, 'ledoge', '⭐', 'Ты звезда!'),
    (20, 'developer', 'Создатель (особый)', 0, 'ledoge', '👑', 'Только для создателя')
]

SKIN_BY_NUMBER = {str(num): (key, name, price, currency, emoji, desc) for num, key, name, price, currency, emoji, desc in ALL_SKINS}

@router.message(F.text == "👕 Магазин скинов")
async def show_skin_shop(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Получаем балансы во всех валютах
    balance_ledoge = get_balance(user_id, 'ledoge')
    balance_bitkoin = get_balance(user_id, 'bitkoin')
    balance_notcoine = get_balance(user_id, 'notcoine')
    balance_shibafloki = get_balance(user_id, 'shibafloki')
    balance_tonkoin = get_balance(user_id, 'tonkoin')
    balance_solanafast = get_balance(user_id, 'solanafast')
    balance_ethireum = get_balance(user_id, 'ethireum')
    
    owned_skins = get_user_owned_skins(user_id)
    current_skin = get_user_skin(user_id)
    
    text = "👕 <b>МАГАЗИН СКИНОВ</b>\n\n"
    text += f"💰 <b>Твой баланс:</b>\n"
    text += f"🐶 LEDOGE: {balance_ledoge:.2f}\n"
    text += f"🪙 BitKoin: {balance_bitkoin:.8f}\n"
    text += f"📱 NotCoine: {balance_notcoine:.2f}\n"
    text += f"🐶 ShibaFloki: {balance_shibafloki:.2f}\n"
    text += f"💎 TonKoin: {balance_tonkoin:.2f}\n"
    text += f"🌲 SolanaFast: {balance_solanafast:.2f}\n"
    text += f"⚡ Ethireum: {balance_ethireum:.2f}\n\n"
    
    text += "📋 <b>Что бы купить скин, напиши его номер в чат:</b>\n\n"
    
    for num, key, name, price, currency, emoji, desc in ALL_SKINS:
        if key == 'developer':
            continue
        
        if key in owned_skins:
            text += f"{num}) {emoji} <b>{name}</b> — (Куплено)\n\n"
        else:
            if currency == 'bitkoin':
                text += f"{num}) {emoji} <b>{name}</b> — {price} 🪙(BitKoin)\n\n"
            elif currency == 'ledoge':
                text += f"{num}) {emoji} <b>{name}</b> — {price} 🐶(LEDOGE)\n\n"
            elif currency == 'notcoine':
                text += f"{num}) {emoji} <b>{name}</b> — {price} 📱(NotCoine)\n\n"
            elif currency == 'shibafloki':
                text += f"{num}) {emoji} <b>{name}</b> — {price} 🐶(ShibaFloki)\n\n"
            elif currency == 'tonkoin':
                text += f"{num}) {emoji} <b>{name}</b> — {price} 💎(TonKoin)\n\n"
            elif currency == 'solanafast':
                text += f"{num}) {emoji} <b>{name}</b> — {price} 🌲(SolanaFast)\n\n"
            elif currency == 'ethireum':
                text += f"{num}) {emoji} <b>{name}</b> — {price} ⚡(Ethireum)\n\n"
            else:
                text += f"{num}) {emoji} <b>{name}</b> — {price} {currency}\n\n"
    
    await message.answer(text, reply_markup=shop_menu())
    await state.set_state(SkinShopStates.waiting_skin_number)

@router.message(F.text == "👕 Шкафчик")
async def show_wardrobe(message: Message, state: FSMContext):
    user_id = message.from_user.id
    owned_skins = get_user_owned_skins(user_id)
    current_skin = get_user_skin(user_id)
    
    if not owned_skins:
        await message.answer("❌ У тебя пока нет купленных скинов!")
        return
    
    text = "👕 <b>ТВОЙ ШКАФЧИК</b>\n\n"
    text += "📋 <b>Что бы надеть скин, напиши его номер в чат:</b>\n\n"
    
    for num, key, name, price, currency, emoji, desc in ALL_SKINS:
        if key in owned_skins:
            if key == current_skin:
                text += f"{num}) {emoji} <b>{name}</b> — (НАДЕТО)\n\n"
            else:
                text += f"{num}) {emoji} <b>{name}</b>\n\n"
    
    await message.answer(text, reply_markup=wardrobe_menu())
    await state.set_state(SkinShopStates.waiting_wardrobe_number)

@router.message(SkinShopStates.waiting_wardrobe_number)
async def process_wardrobe_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Проверяем кнопки навигации
    if text == "❌ Снять скин":
        current = get_user_skin(user_id)
        if current == 'none':
            await message.answer("❌ На тебе нет скина!")
            return
        
        remove_skin(user_id)
        await message.answer("✅ Скин снят! Ты теперь обычный пользователь.")
        await show_wardrobe(message, state)
        return
    
    elif text == "◀ Назад в магазин":
        await show_skin_shop(message, state)
        return
    
    elif text == "◀ Назад в меню":
        await state.clear()
        from handlers.common import back_to_menu
        await back_to_menu(message)
        return
    
    # Проверяем, не являются ли это кнопками из главного меню
    elif text in ["🤝 Рефералы", "📈 Курсы валют", "💰 Криптокошелёк", "⛏ Майнинг", 
                  "☝ Тапалка", "💱 Обменник", "🏪 P2P Биржа", "🎰 Колесо фортуны",
                  "📊 Топ майнеров", "ℹ Обучение", "🔗 Канал и поддержка"]:
        await state.clear()
        return
    
    # Проверяем номер
    if text not in SKIN_BY_NUMBER:
        await message.answer("❌ Неправильный номер. Введи число от 1 до 19")
        return
    
    skin_num = text
    key, name, price, currency, emoji, desc = SKIN_BY_NUMBER[skin_num]
    
    # Проверяем, есть ли этот скин у пользователя
    owned_skins = get_user_owned_skins(user_id)
    if key not in owned_skins:
        await message.answer("❌ У тебя нет этого скина! Сначала купи его в магазине.")
        return
    
    temp_skin_choice[user_id] = key
    
    text = (
        f"<b>Хотите надеть этот скин?</b>\n\n"
        f"{emoji} <b>{name}</b>\n"
        f"<i>{desc}</i>"
    )
    
    await message.answer(text, reply_markup=yes_no_menu())
    await state.set_state(SkinShopStates.waiting_equip_confirm)

@router.message(SkinShopStates.waiting_skin_number)
async def process_skin_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Проверяем кнопки навигации
    if text == "👕 Шкафчик":
        await show_wardrobe(message, state)
        return
    elif text == "◀ Назад в меню":
        await state.clear()
        from handlers.common import back_to_menu
        await back_to_menu(message)
        return
    
    # Проверяем, не являются ли это кнопками из главного меню
    elif text in ["🤝 Рефералы", "📈 Курсы валют", "💰 Криптокошелёк", "⛏ Майнинг", 
                  "☝ Тапалка", "💱 Обменник", "🏪 P2P Биржа", "🎰 Колесо фортуны",
                  "📊 Топ майнеров", "ℹ Обучение", "🔗 Канал и поддержка"]:
        await state.clear()
        return
    
    # Проверяем номер
    if text not in SKIN_BY_NUMBER:
        await message.answer("❌ Неправильный номер. Введи число от 1 до 19")
        return
    
    skin_num = text
    key, name, price, currency, emoji, desc = SKIN_BY_NUMBER[skin_num]
    
    # Проверяем, есть ли уже скин
    owned_skins = get_user_owned_skins(user_id)
    if key in owned_skins:
        await message.answer(
            f"❌ У вас уже есть этот скин, примерьте его в шкафчике!",
            reply_markup=shop_menu()
        )
        return
    
    temp_skin_choice[user_id] = key
    
    balance = get_balance(user_id, currency)
    currency_names = {
        'ledoge': '🐶 LEDOGE',
        'bitkoin': '🪙 BitKoin',
        'notcoine': '📱 NotCoine',
        'shibafloki': '🐶 ShibaFloki',
        'tonkoin': '💎 TonKoin',
        'solanafast': '🌲 SolanaFast',
        'ethireum': '⚡ Ethireum'
    }
    currency_name = currency_names.get(currency, currency.upper())
    
    text = (
        f"{emoji} <b>{name}</b> — {price} {currency_name}\n\n"
        f"<i>{desc}</i>\n\n"
        f"Купить скин?"
    )
    
    await message.answer(text, reply_markup=yes_no_menu())
    await state.set_state(SkinShopStates.waiting_buy_confirm)

@router.message(SkinShopStates.waiting_buy_confirm)
async def process_buy_confirm(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "✅ Да":
        skin_key = temp_skin_choice.get(user_id)
        if not skin_key:
            await message.answer("❌ Ошибка, попробуй снова")
            await state.clear()
            return
        
        success, msg = buy_skin(user_id, skin_key)
        await message.answer(msg)
        
        if success:
            await message.answer(
                f"✅ Скин куплен! Ты можешь надеть его в шкафчике.",
                reply_markup=shop_menu()
            )
        await state.clear()
        await show_skin_shop(message, state)
            
    elif text == "❌ Нет":
        await message.answer("❌ Покупка отменена", reply_markup=shop_menu())
        await state.clear()
    else:
        await message.answer("❌ Используй кнопки Да или Нет")
        return

@router.message(SkinShopStates.waiting_equip_confirm)
async def process_equip_confirm(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "✅ Да":
        skin_key = temp_skin_choice.get(user_id)
        if not skin_key:
            await message.answer("❌ Ошибка, попробуй снова")
            await state.clear()
            return
        
        success, msg = equip_skin(user_id, skin_key)
        await message.answer(msg)
        await state.clear()
        await show_wardrobe(message, state)
        
    elif text == "❌ Нет":
        await message.answer("❌ Отменено")
        await state.clear()
        await show_wardrobe(message, state)
    else:
        await message.answer("❌ Используй кнопки Да или Нет")
        return

@router.message(F.text == "◀ Назад в магазин")
async def back_to_shop(message: Message, state: FSMContext):
    await show_skin_shop(message, state)

@router.message(F.text == "◀ Назад в меню")
async def back_to_main(message: Message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        from keyboards import admin_keyboard
        await message.answer("🔧 Админ-меню:", reply_markup=admin_keyboard())
    else:
        await message.answer("Главное меню:", reply_markup=main_menu())