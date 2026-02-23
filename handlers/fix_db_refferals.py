# fix_db_referrer.py
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = 'crypto_sim.db'

def fix_database():
    """Добавляет колонку referrer_id в таблицу users"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    logger.info("🔄 Проверка структуры базы данных...")
    
    # Проверяем существование колонки referrer_id
    cur.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'referrer_id' not in columns:
        logger.info("➕ Добавление колонки referrer_id в таблицу users...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0")
            logger.info("✅ Колонка referrer_id успешно добавлена")
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении колонки: {e}")
    else:
        logger.info("✅ Колонка referrer_id уже существует")
    
    # Проверяем существование таблицы referrals
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if not cur.fetchone():
        logger.info("➕ Создание таблицы referrals...")
        cur.execute('''
            CREATE TABLE referrals (
                referrer_id INTEGER,
                referral_id INTEGER,
                referral_date TEXT,
                total_earned REAL DEFAULT 0,
                PRIMARY KEY (referrer_id, referral_id)
            )
        ''')
        logger.info("✅ Таблица referrals создана")
    else:
        logger.info("✅ Таблица referrals уже существует")
    
    conn.commit()
    conn.close()
    
    logger.info("✅ База данных успешно обновлена!")

if __name__ == "__main__":
    fix_database()