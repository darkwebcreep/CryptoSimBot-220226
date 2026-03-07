# config.py
import os
import logging

logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', "8347994225:AAEYhgaxSlo-xJcJm8ciVwBjkBep2WY_Iwo")
ADMIN_ID = int(os.getenv('ADMIN_ID', "1050769466"))

logger.info(f"⚙️ Загружена конфигурация: ADMIN_ID={ADMIN_ID}")

# Ссылки
CHANNEL_LINK = "https://t.me/LEDOGEchannel"
SUPPORT_LINK = "https://t.me/woolfcreep"

# ============= КУРСЫ ВАЛЮТ =============
CURRENCY_PRICES = {
    'notcoine': 0.001,
    'shibafloki': 0.002,
    'solanafast': 0.05,
    'tonkoin': 0.1,
    'dodgecoin': 0.15,
    'ethireum': 1.5,
    'bitkoin': 50000.0,
    'ledoge': 0.01,
    'usdtoken': 1.0
}

# Комиссии
GAS_FEES = {
    'sell': 0.01,
    'buy': 0.01,
    'transfer': 0.005
}

# Названия валют
CURRENCIES = {
    'ledoge': '🐶 LEDOGE',
    'bitkoin': '🪙 BitKoin',
    'notcoine': '📱 NotCoine',
    'ethireum': '⚡ Ethireum',
    'dodgecoin': '🐕 DodgeCoin',
    'tonkoin': '💎 TonKoin',
    'solanafast': '🌲 SolanaFast',
    'riplcoin': '💧 RiplCoin',
    'usdtoken': '💵 USDToken',
    'shibafloki': '🐶 ShibaFloki'
}

# ============= СКИНЫ =============
SKINS = {
    'bronze': {'name': '🥉 Бронзовая кость', 'price': 500, 'currency': 'ledoge', 'emoji': '🦴', 'desc': 'Простая кость для простых людей'},
    'silver': {'name': '🥈 Серебряный бульдог', 'price': 2000, 'currency': 'ledoge', 'emoji': '🐕', 'desc': 'Серебро всегда в цене'},
    'gold': {'name': '🥇 Золотой бульдог', 'price': 5000, 'currency': 'ledoge', 'emoji': '👑', 'desc': 'Король крипты!'},
    'diamond': {'name': '💎 Бриллиантовый бульдог', 'price': 10000, 'currency': 'ledoge', 'emoji': '💎', 'desc': 'Бриллиантовая ручка'},
    'satoshi': {'name': '👤 Satoshi Nakamoto', 'price': 10, 'currency': 'bitkoin', 'emoji': '👤', 'desc': 'Никто не узнает кто ты'},
    'joseph': {'name': '🐺 Джозеф', 'price': 50, 'currency': 'ledoge', 'emoji': '🐺', 'desc': 'Это будет замечательный день, замечательный...'},
    'enlightened': {'name': '📖 Просвещённый', 'price': 10, 'currency': 'ledoge', 'emoji': '📖', 'desc': 'Тяжело в учении - легко в бою!'},
    'bateman': {'name': '🪓 Патрик Бейтман', 'price': 20, 'currency': 'ledoge', 'emoji': '🪓', 'desc': 'Я люблю свою работу. Она приносит мне кучу денег.'},
    'autoclicker': {'name': '👆 АвтоКликер', 'price': 1000, 'currency': 'notcoine', 'emoji': '👆', 'desc': 'Самый быстрый палец на диком западе'},
    'hachiko': {'name': '😞 Хатико', 'price': 10000, 'currency': 'shibafloki', 'emoji': '😞', 'desc': 'Я буду ждать торги...'},
    'heisenberg': {'name': '👨‍🔬 Хайзенберг', 'price': 10, 'currency': 'tonkoin', 'emoji': '👨‍🔬', 'desc': 'Скажи моё имя'},
    'superpepper': {'name': '🌶️ Суперперец!', 'price': 5, 'currency': 'tonkoin', 'emoji': '🌶️', 'desc': 'Почему только это и Мухаммед?!'},
    'belfort': {'name': '💵 Джордан Белфорт', 'price': 500000, 'currency': 'ledoge', 'emoji': '💵', 'desc': '22 миллиона долларов за 3 грёбаных часа!'},
    'sonic': {'name': '🦔 Соник', 'price': 1000000, 'currency': 'notcoine', 'emoji': '🦔', 'desc': 'Они зовут меня Соник'},
    'error404': {'name': '🚫 404', 'price': 2, 'currency': 'solanafast', 'emoji': '🚫', 'desc': 'ERROR'},
    'hamster': {'name': '🐹 Хомяк', 'price': 10, 'currency': 'notcoine', 'emoji': '🐹', 'desc': 'Тап Тап Тап по хомяку'},
    'angrybird': {'name': '🐦 Злая птичка', 'price': 1, 'currency': 'solanafast', 'emoji': '🐦', 'desc': 'Я играю в энгри бёрдс'},
    'greedy': {'name': '🤑 Алчный', 'price': 100, 'currency': 'ethireum', 'emoji': '🤑', 'desc': 'Бабки, бабки песик, БАБКИ!'},
    'star': {'name': '⭐ Звёздный игрок!', 'price': 12, 'currency': 'ledoge', 'emoji': '⭐', 'desc': 'Ты звезда!'},
    'developer': {'name': '👑 Создатель (особый)', 'price': 0, 'currency': 'ledoge', 'emoji': '👑', 'desc': 'Только для создателя'},
    'march_8_2026': {
        'name': '🌸 Весенний 2026', 
        'price': 888, 
        'currency': 'ledoge', 
        'emoji': '🌸', 
        'desc': 'Праздничный скин в честь 8 Марта 2026'
    }
}

# ============= НАСТРОЙКИ РЕФЕРАЛЬНОЙ СИСТЕМЫ =============
REFERRAL_SETTINGS = {
    'reward_for_invite': 500,
    'reward_percent_first_day': 0.10,
    'reward_percent_permanent': 0.05,
    'min_payout': 10,
    'referral_bonus_days': 7
}

# Бустеры
TAP_BOOSTERS = {
    'x2': {'name': '✨ x2 Множитель', 'price': 100, 'multiplier': 2, 'duration': 3600},
    'x3': {'name': '🔥 x3 Множитель', 'price': 250, 'multiplier': 3, 'duration': 3600},
    'x4': {'name': '⚡ x4 Множитель', 'price': 500, 'multiplier': 4, 'duration': 3600},
    'x5': {'name': '💎 x5 Множитель', 'price': 1000, 'multiplier': 5, 'duration': 3600}
}

ENERGY_BOOSTERS = {
    'small': {'name': '🔋 Малая энергия', 'price': 50, 'energy': 50},
    'medium': {'name': '⚡ Средняя энергия', 'price': 120, 'energy': 150},
    'large': {'name': '💪 Большая энергия', 'price': 200, 'energy': 300},
    'max': {'name': '🚀 Максимальная энергия', 'price': 350, 'energy': 500}
}

# Майнеры
MINERS = {
    'usb': {'name': '💻 USB майнер', 'price': 100, 'bonus': 0.05, 'description': 'Увеличивает шанс майнинга на 5%', 'emoji': '🔌'},
    'smartphone': {'name': '📱 Смартфон майнер', 'price': 350, 'bonus': 0.10, 'description': 'Увеличивает шанс майнинга на 10%', 'emoji': '📱'},
    'fpga': {'name': '🔷 FPGA майнер', 'price': 1000, 'bonus': 0.15, 'description': 'Увеличивает шанс майнинга на 15%', 'emoji': '🔷'},
    'cpu': {'name': '🖥️ CPU майнер', 'price': 2500, 'bonus': 0.20, 'description': 'Увеличивает шанс майнинга на 20%', 'emoji': '🖥️'},
    'gpu': {'name': '🎮 GPU майнер', 'price': 5000, 'bonus': 0.25, 'description': 'Увеличивает шанс майнинга на 25%', 'emoji': '🎮'},
    'asic': {'name': '⚙️ ASIC майнер', 'price': 12000, 'bonus': 0.35, 'description': 'Увеличивает шанс майнинга на 35%', 'emoji': '⚙️'}
}
