# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = [
        [KeyboardButton(text="💰 Криптокошелёк")],
        [KeyboardButton(text="⛏ Майнинг"), KeyboardButton(text="☝ Тапалка")],
        [KeyboardButton(text="💱 Обменник"), KeyboardButton(text="🏪 P2P Биржа")],
        [KeyboardButton(text="🎰 Колесо фортуны"), KeyboardButton(text="👕 Магазин скинов")],
        [KeyboardButton(text="🤝 Рефералы"), KeyboardButton(text="📈 Курсы валют")],
        [KeyboardButton(text="📊 Топ майнеров"), KeyboardButton(text="ℹ Обучение")],
        [KeyboardButton(text="🔗 Канал и поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def mining_menu():
    kb = [
        [KeyboardButton(text="🪙 Майнить BitKoin (сложно)")],
        [KeyboardButton(text="⚡ Майнить Ethireum")],
        [KeyboardButton(text="🐕 Майнить DodgeCoin")],
        [KeyboardButton(text="💎 Майнить TonKoin")],
        [KeyboardButton(text="🌲 Майнить SolanaFast")],
        [KeyboardButton(text="⚙️ Майнеры")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def tap_menu():
    kb = [
        [KeyboardButton(text="📱 Тапать NotCoine")],
        [KeyboardButton(text="🐶 Тапать ShibaFloki")],
        [KeyboardButton(text="✨ Бустеры")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def boosters_menu():
    kb = [
        [KeyboardButton(text="✨ x2 множитель - 100")],
        [KeyboardButton(text="🔥 x3 множитель - 250")],
        [KeyboardButton(text="⚡ x4 множитель - 500")],
        [KeyboardButton(text="💎 x5 множитель - 1000")],
        [KeyboardButton(text="🔋 Малая энергия +50 - 50")],
        [KeyboardButton(text="⚡ Средняя энергия +150 - 120")],
        [KeyboardButton(text="💪 Большая энергия +300 - 200")],
        [KeyboardButton(text="🚀 Макс. энергия +500 - 350")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def miners_menu():
    kb = [
        [KeyboardButton(text="🔌 USB майнер - 100")],
        [KeyboardButton(text="📱 Смартфон майнер - 350")],
        [KeyboardButton(text="🔷 FPGA майнер - 1000")],
        [KeyboardButton(text="🖥️ CPU майнер - 2500")],
        [KeyboardButton(text="🎮 GPU майнер - 5000")],
        [KeyboardButton(text="⚙️ ASIC майнер - 12000")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def exchange_p2p_menu():
    kb = [
        [KeyboardButton(text="💰 Продать монету")],
        [KeyboardButton(text="🛒 Купить монету")],
        [KeyboardButton(text="🎁 Перевести другу")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def shop_menu():
    kb = [
        [KeyboardButton(text="👕 Шкафчик")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def wardrobe_menu():
    kb = [
        [KeyboardButton(text="❌ Снять скин")],
        [KeyboardButton(text="◀ Назад в магазин")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def yes_no_menu():
    kb = [
        [KeyboardButton(text="✅ Да")],
        [KeyboardButton(text="❌ Нет")],
        [KeyboardButton(text="👕 Шкафчик")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def wheel_keyboard():
    kb = [
        [InlineKeyboardButton(text="🎲 Крутить за 10 LEDOGE", callback_data="wheel_spin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_keyboard():
    kb = [
        [KeyboardButton(text="🔧 Выдать монеты")],
        [KeyboardButton(text="📢 Сделать рассылку")],
        [KeyboardButton(text="📊 Статистика бота")],
        [KeyboardButton(text="👤 Режим пользователя")],
        [KeyboardButton(text="👑 Особый скин")],
        [KeyboardButton(text="◀ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)