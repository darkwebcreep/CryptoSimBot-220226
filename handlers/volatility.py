# handlers/volatility.py
import asyncio
import random
import logging
from datetime import datetime
from config import CURRENCY_PRICES, VOLATILITY_SETTINGS
from database import get_connection

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения цен
current_prices = CURRENCY_PRICES.copy()
last_update = datetime.now()

async def update_prices():
    """Фоновая задача для обновления цен"""
    global current_prices, last_update
    
    while True:
        try:
            await asyncio.sleep(VOLATILITY_SETTINGS['update_interval'])
            
            old_prices = current_prices.copy()
            event_message = ""
            
            # Проверяем особые события
            if random.random() < VOLATILITY_SETTINGS['crash_chance']:
                multiplier = VOLATILITY_SETTINGS['crash_multiplier']
                event_message = "💥 РЫНОК ОБРУШИЛСЯ! Все цены упали на 50%!"
                for currency in current_prices:
                    current_prices[currency] *= multiplier
            
            elif random.random() < VOLATILITY_SETTINGS['moon_chance']:
                multiplier = VOLATILITY_SETTINGS['moon_multiplier']
                event_message = "🚀 ЛУНА! Цены взлетели в 2 раза!"
                for currency in current_prices:
                    current_prices[currency] *= multiplier
            
            else:
                for currency in current_prices:
                    change = random.uniform(
                        -VOLATILITY_SETTINGS['max_change'],
                        VOLATILITY_SETTINGS['max_change']
                    )
                    current_prices[currency] *= (1 + change)
                    if current_prices[currency] < 0.0001:
                        current_prices[currency] = 0.0001
            
            await save_price_history()
            last_update = datetime.now()
            
            log_changes(old_prices, current_prices, event_message)
            
        except Exception as e:
            logger.error(f"Ошибка в update_prices: {e}")
            await asyncio.sleep(60)

def log_changes(old_prices, new_prices, event_message):
    """Логирует изменения цен"""
    logger.info("=" * 50)
    if event_message:
        logger.info(event_message)
    logger.info("📊 Изменение цен:")
    for currency in new_prices:
        old = old_prices[currency]
        new = new_prices[currency]
        change = ((new - old) / old) * 100
        arrow = "📈" if change > 0 else "📉"
        logger.info(f"  {currency}: {old:.4f} → {new:.4f} {arrow} {change:+.1f}%")
    logger.info("=" * 50)

async def save_price_history():
    """Сохраняет текущие цены в историю"""
    conn = get_connection()
    cur = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    for currency, price in current_prices.items():
        cur.execute('''
            INSERT INTO price_history (currency, price, timestamp)
            VALUES (?, ?, ?)
        ''', (currency, price, timestamp))
    
    conn.commit()
    conn.close()

def get_current_prices():
    """Возвращает текущие цены"""
    return current_prices

def get_price(currency):
    """Возвращает цену конкретной валюты"""
    return current_prices.get(currency, 0)