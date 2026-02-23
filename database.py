# database.py
import sqlite3
import json
import logging
import threading
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger('database')

DB_NAME = 'crypto_sim.db'
_local = threading.local()

def get_connection():
    """Получает новое соединение с БД"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """Универсальная функция для выполнения запросов"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        
        if fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()
        else:
            conn.commit()
            result = True
            
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка запроса: {query[:100]}... {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Создаёт таблицы при первом запуске"""
    try:
        # Таблица пользователей
        execute_query('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_date TEXT,
                skin TEXT DEFAULT 'none',
                owned_skins TEXT DEFAULT '[]',
                wheel_spins INTEGER DEFAULT 0,
                wheel_wins INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                last_tap_time TEXT,
                tap_multiplier REAL DEFAULT 1.0,
                booster_expiry TEXT,
                referrer_id INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица с балансами
        execute_query('''
            CREATE TABLE IF NOT EXISTS balances (
                user_id INTEGER PRIMARY KEY,
                balances TEXT DEFAULT '{}'
            )
        ''')
        
        # Таблица с майнерами
        execute_query('''
            CREATE TABLE IF NOT EXISTS miners (
                user_id INTEGER,
                miner_type TEXT,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, miner_type)
            )
        ''')
        
        # Таблица рефералов
        execute_query('''
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referral_id INTEGER,
                referral_date TEXT,
                total_earned REAL DEFAULT 0,
                PRIMARY KEY (referrer_id, referral_id)
            )
        ''')
        
        # Таблица для истории цен
        execute_query('''
            CREATE TABLE IF NOT EXISTS price_history (
                currency TEXT,
                price REAL,
                timestamp TEXT,
                PRIMARY KEY (currency, timestamp)
            )
        ''')
        
        # Индексы
        execute_query('CREATE INDEX IF NOT EXISTS idx_users_id ON users(user_id)')
        execute_query('CREATE INDEX IF NOT EXISTS idx_balances_user ON balances(user_id)')
        execute_query('CREATE INDEX IF NOT EXISTS idx_miners_user ON miners(user_id)')
        execute_query('CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)')
        
        logger.info("✅ Инициализация БД завершена")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}", exc_info=True)
        raise

# ==================== ПОЛЬЗОВАТЕЛИ ====================

@lru_cache(maxsize=128)
def get_user_cached(user_id):
    """Кэшированный запрос пользователя"""
    return execute_query('SELECT * FROM users WHERE user_id = ?', (user_id,), fetch_one=True)

def clear_cache():
    """Очищает кэш"""
    get_user_cached.cache_clear()
    get_balance_cached.cache_clear()

def user_exists(user_id):
    """Проверяет, существует ли пользователь"""
    try:
        result = execute_query('SELECT user_id FROM users WHERE user_id = ?', (user_id,), fetch_one=True)
        return result is not None
    except Exception as e:
        logger.error(f"Ошибка при проверке существования пользователя {user_id}: {e}")
        return False

def create_user(user_id, username=None, first_name=None, referrer_id=0):
    """Создает нового пользователя"""
    logger.info(f"👤 Создание нового пользователя {username or first_name} (ID: {user_id})")
    try:
        # Создаем пользователя
        execute_query('''
            INSERT INTO users 
            (user_id, username, first_name, registered_date, skin, owned_skins, 
             energy, max_energy, tap_multiplier, referrer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat(), 
              'none', '[]', 100, 100, 1.0, referrer_id))
        
        # Создаем пустой баланс
        execute_query('INSERT INTO balances (user_id, balances) VALUES (?, ?)', 
                     (user_id, '{}'))
        
        clear_cache()
        logger.info(f"✅ Пользователь {user_id} успешно создан")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при создании пользователя {user_id}: {e}")
        return False

def get_user(user_id, username=None, first_name=None, referrer_id=0):
    """Получает пользователя из БД или создаёт нового"""
    try:
        # Проверяем существование пользователя
        if not user_exists(user_id):
            logger.info(f"👤 Пользователь {user_id} не найден, создаем...")
            success = create_user(user_id, username, first_name, referrer_id)
            if not success:
                logger.error(f"❌ Не удалось создать пользователя {user_id}")
                return None
        
        # Получаем данные пользователя
        user = execute_query('SELECT * FROM users WHERE user_id = ?', (user_id,), fetch_one=True)
        
        if user:
            logger.debug(f"✅ Пользователь {user_id} найден")
            return user
        else:
            logger.error(f"❌ Пользователь {user_id} не найден после создания")
            return None
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в get_user для {user_id}: {e}")
        return None

# ==================== БАЛАНСЫ ====================

@lru_cache(maxsize=256)
def get_balance_cached(user_id, currency='ledoge'):
    """Кэшированный баланс"""
    result = execute_query('SELECT balances FROM balances WHERE user_id = ?', (user_id,), fetch_one=True)
    
    if result and result[0]:
        try:
            balances = json.loads(result[0])
            return balances.get(currency, 0)
        except:
            return 0
    return 0

def get_balance(user_id, currency='ledoge'):
    return get_balance_cached(user_id, currency)

def update_balance(user_id, currency, amount, operation='add'):
    """Обновляет баланс"""
    result = execute_query('SELECT balances FROM balances WHERE user_id = ?', (user_id,), fetch_one=True)
    
    if result:
        balances = json.loads(result[0])
        current = balances.get(currency, 0)
        
        if operation == 'add':
            balances[currency] = current + amount
        elif operation == 'subtract':
            if current >= amount:
                balances[currency] = current - amount
            else:
                return False
        
        execute_query('UPDATE balances SET balances = ? WHERE user_id = ?', 
                     (json.dumps(balances), user_id))
        get_balance_cached.cache_clear()
        return True
    return False

# ==================== ЭНЕРГИЯ ====================

def get_user_energy(user_id):
    """Получает текущую энергию пользователя"""
    try:
        result = execute_query('SELECT energy, max_energy, last_tap_time FROM users WHERE user_id = ?', 
                              (user_id,), fetch_one=True)
        
        if result:
            energy = result[0] if result[0] is not None else 100
            max_energy = result[1] if result[1] is not None else 100
            last_tap = result[2]
            
            if last_tap:
                try:
                    last = datetime.fromisoformat(last_tap)
                    minutes_passed = (datetime.now() - last).seconds // 60
                    if minutes_passed > 0:
                        energy = min(max_energy, energy + minutes_passed)
                        execute_query('UPDATE users SET energy = ? WHERE user_id = ?', (energy, user_id))
                except:
                    pass
            
            return energy, max_energy
    except Exception as e:
        logger.error(f"Ошибка в get_user_energy: {e}")
    
    return 100, 100

def use_energy(user_id, amount=1):
    """Использует энергию"""
    energy, max_energy = get_user_energy(user_id)
    
    if energy >= amount:
        new_energy = energy - amount
        execute_query('UPDATE users SET energy = ?, last_tap_time = ? WHERE user_id = ?',
                     (new_energy, datetime.now().isoformat(), user_id))
        return True, new_energy
    
    return False, energy

def add_max_energy(user_id, amount):
    """Увеличивает максимальную энергию"""
    execute_query('UPDATE users SET max_energy = max_energy + ? WHERE user_id = ?', (amount, user_id))
    clear_cache()

# ==================== БУСТЕРЫ ====================

def get_user_booster(user_id):
    """Получает информацию о бустере пользователя"""
    try:
        result = execute_query('SELECT tap_multiplier, booster_expiry FROM users WHERE user_id = ?', 
                              (user_id,), fetch_one=True)
        
        if result and result[0] is not None:
            multiplier = result[0]
            expiry_str = result[1]
            
            if expiry_str:
                try:
                    expiry = datetime.fromisoformat(expiry_str)
                    if datetime.now() < expiry:
                        return {'multiplier': multiplier, 'expiry': expiry}
                except:
                    pass
            
            return {'multiplier': multiplier, 'expiry': None}
    except Exception as e:
        logger.error(f"Ошибка в get_user_booster: {e}")
    
    return {'multiplier': 1.0, 'expiry': None}

def set_user_booster(user_id, multiplier, duration_seconds):
    """Устанавливает бустер пользователю"""
    try:
        expiry = (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
        execute_query('UPDATE users SET tap_multiplier = ?, booster_expiry = ? WHERE user_id = ?',
                     (multiplier, expiry, user_id))
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Ошибка в set_user_booster: {e}")
        return False

# ==================== МАЙНЕРЫ ====================

def get_user_miners(user_id):
    """Получает список майнеров пользователя"""
    results = execute_query('SELECT miner_type, quantity FROM miners WHERE user_id = ?', 
                           (user_id,), fetch_all=True)
    miners = {}
    if results:
        for row in results:
            miners[row[0]] = row[1]
    return miners

def get_miner_bonus(user_id):
    """Получает общий бонус к майнингу от всех майнеров"""
    from config import MINERS
    
    miners = get_user_miners(user_id)
    total_bonus = 1.0
    
    for miner_type, quantity in miners.items():
        if miner_type in MINERS:
            bonus = MINERS[miner_type].get('bonus', 0.05) * quantity
            total_bonus += bonus
    
    return total_bonus

def buy_miner(user_id, miner_type, price):
    """Покупает майнера"""
    from config import MINERS
    
    if miner_type not in MINERS:
        return False, "Майнер не найден"
    
    if get_balance(user_id, 'ledoge') < price:
        return False, f"❌ Недостаточно LEDOGE. Нужно: {price}"
    
    if not update_balance(user_id, 'ledoge', price, 'subtract'):
        return False, "❌ Ошибка при списании"
    
    # Проверяем, есть ли уже такой майнер
    existing = execute_query('SELECT quantity FROM miners WHERE user_id = ? AND miner_type = ?',
                            (user_id, miner_type), fetch_one=True)
    
    if existing:
        execute_query('UPDATE miners SET quantity = quantity + 1 WHERE user_id = ? AND miner_type = ?',
                     (user_id, miner_type))
    else:
        execute_query('INSERT INTO miners (user_id, miner_type, quantity) VALUES (?, ?, 1)',
                     (user_id, miner_type))
    
    bonus = MINERS[miner_type].get('bonus', 0.05) * 100
    return True, f"✅ Куплен {MINERS[miner_type]['name']}! Шанс майнинга увеличен на +{bonus}%"

# ==================== СКИНЫ ====================

def get_user_owned_skins(user_id):
    """Получает список всех скинов, которые есть у пользователя"""
    result = execute_query('SELECT owned_skins FROM users WHERE user_id = ?', (user_id,), fetch_one=True)
    
    if result and result[0]:
        try:
            return json.loads(result[0])
        except:
            return []
    return []

def add_skin_to_wardrobe(user_id, skin_key):
    """Добавляет скин в шкафчик пользователя"""
    owned = get_user_owned_skins(user_id)
    if skin_key not in owned:
        owned.append(skin_key)
        execute_query('UPDATE users SET owned_skins = ? WHERE user_id = ?', 
                     (json.dumps(owned), user_id))
        clear_cache()
    return owned

def equip_skin(user_id, skin_key):
    """Надевает скин"""
    from config import SKINS
    
    owned = get_user_owned_skins(user_id)
    if skin_key not in owned and skin_key != 'developer':
        return False, "❌ У тебя нет этого скина"
    
    execute_query('UPDATE users SET skin = ? WHERE user_id = ?', (skin_key, user_id))
    clear_cache()
    return True, f"✅ Теперь надет {SKINS[skin_key]['name']}!"

def get_user_skin(user_id):
    """Получает текущий надетый скин"""
    user = get_user_cached(user_id)
    if user and len(user) > 4:
        return user[4]
    return 'none'

def buy_skin(user_id, skin_key):
    """Покупка скина"""
    from config import SKINS, ADMIN_ID
    
    skin_data = SKINS.get(skin_key)
    if not skin_data:
        return False, "Скин не найден"
    
    if skin_key == 'developer' and user_id != ADMIN_ID:
        return False, "❌ Этот скин только для создателя!"
    
    price = skin_data['price']
    currency = skin_data.get('currency', 'ledoge')
    
    if get_balance(user_id, currency) < price:
        return False, f"❌ Недостаточно {currency.upper()}. Нужно: {price}"
    
    if not update_balance(user_id, currency, price, 'subtract'):
        return False, "❌ Ошибка при списании"
    
    add_skin_to_wardrobe(user_id, skin_key)
    
    return True, f"✅ Ты купил {skin_data['name']}! Он добавлен в шкафчик."

def remove_skin(user_id):
    """Снимает скин"""
    execute_query('UPDATE users SET skin = ? WHERE user_id = ?', ('none', user_id))
    clear_cache()

# ==================== КОМИССИИ ====================

def calculate_gas(amount, operation_type='buy'):
    """Рассчитывает комиссию (газ) для операции"""
    from config import GAS_FEES
    fee_percent = GAS_FEES.get(operation_type, 0.01)
    return amount * fee_percent

# ==================== КОЛЕСО ФОРТУНЫ ====================

def spin_wheel(user_id, bet_currency='ledoge', bet_amount=10):
    """Крутит колесо фортуны"""
    from random import random
    
    if get_balance(user_id, bet_currency) < bet_amount:
        return False, "❌ Недостаточно средств", 0
    
    if not update_balance(user_id, bet_currency, bet_amount, 'subtract'):
        return False, "❌ Ошибка при списании", 0
    
    execute_query('UPDATE users SET wheel_spins = wheel_spins + 1 WHERE user_id = ?', (user_id,))
    
    chance = random()
    
    if chance < 0.01:
        win = bet_amount * 10
        execute_query('UPDATE users SET wheel_wins = wheel_wins + 1 WHERE user_id = ?', (user_id,))
        update_balance(user_id, bet_currency, win, 'add')
        return True, "🎉 ДЖЕКПОТ! x10", win
    elif chance < 0.10:
        win = bet_amount * 3
        execute_query('UPDATE users SET wheel_wins = wheel_wins + 1 WHERE user_id = ?', (user_id,))
        update_balance(user_id, bet_currency, win, 'add')
        return True, "🎊 Большой выигрыш! x3", win
    elif chance < 0.40:
        win = int(bet_amount * 1.5)
        execute_query('UPDATE users SET wheel_wins = wheel_wins + 1 WHERE user_id = ?', (user_id,))
        update_balance(user_id, bet_currency, win, 'add')
        return True, "😊 Малый выигрыш! x1.5", win
    else:
        return True, "😢 Проигрыш... Повезёт в следующий раз!", 0

# ==================== ТОП ПОЛЬЗОВАТЕЛЕЙ ====================

# database.py (замени существующую функцию get_top_users)

def get_top_users(limit=10):
    """Топ пользователей по балансу LEDOGE (показывает всех игроков)"""
    try:
        # Получаем всех пользователей с их балансами
        users_data = execute_query('''
            SELECT users.user_id, users.username, users.first_name, users.skin, balances.balances
            FROM users
            LEFT JOIN balances ON users.user_id = balances.user_id
            ORDER BY users.user_id DESC
        ''', fetch_all=True)
        
        if not users_data:
            logger.info("📭 Нет пользователей в базе данных")
            return []
        
        users = []
        for row in users_data:
            try:
                user_id = row[0]
                username = row[1]
                first_name = row[2] or "Без имени"
                skin = row[3] or 'none'
                balances_json = row[4]
                
                # Парсим балансы
                if balances_json:
                    balances = json.loads(balances_json)
                    ledoge_balance = balances.get('ledoge', 0)
                else:
                    ledoge_balance = 0
                
                # Добавляем ВСЕХ пользователей, даже с нулевым балансом
                users.append({
                    'user_id': user_id,
                    'username': username,
                    'first_name': first_name,
                    'skin': skin,
                    'ledoge': ledoge_balance
                })
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке пользователя {row[0]}: {e}")
                continue
        
        # Сортируем по убыванию LEDOGE (те, у кого больше, будут выше)
        users.sort(key=lambda x: x['ledoge'], reverse=True)
        
        # Логируем результат для отладки
        logger.info(f"📊 Всего пользователей в БД: {len(users)}")
        if users:
            logger.info(f"🏆 Лидер: {users[0]['first_name']} с балансом {users[0]['ledoge']:.2f} LEDOGE")
            # Покажем первых 3 для примера
            for i, u in enumerate(users[:3]):
                logger.info(f"   {i+1}. {u['first_name']} - {u['ledoge']:.2f} LEDOGE")
        
        return users[:limit]
        
    except Exception as e:
        logger.error(f"❌ Ошибка в get_top_users: {e}")
        return []

# ==================== РЕФЕРАЛЫ ====================

def get_referral_stats(user_id):
    """Получает статистику рефералов пользователя"""
    result = execute_query('SELECT COUNT(*), SUM(total_earned) FROM referrals WHERE referrer_id = ?', 
                          (user_id,), fetch_one=True)
    
    return {
        'count': result[0] or 0,
        'total_earned': result[1] or 0
    }

def get_referrals_list(user_id):
    """Получает список рефералов пользователя"""
    return execute_query('''
        SELECT referral_id, referral_date, total_earned 
        FROM referrals 
        WHERE referrer_id = ?
        ORDER BY referral_date DESC
    ''', (user_id,), fetch_all=True)
