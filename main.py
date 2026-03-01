# main.py
import asyncio
import logging
import sys
import os
import signal
import time
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramConflictError

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from handlers import common, mining, shop, admin, exchange, skinshop, referral, price_watch
from handlers.volatility import update_prices
from middlewares import ThrottlingMiddleware

# ==================== ФАЙЛ БЛОКИРОВКИ ====================
LOCK_FILE = "bot.lock"

def check_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = f.read().strip()
            if os.name == 'nt':
                import subprocess
                result = subprocess.run(f'tasklist /FI "PID eq {pid}"', capture_output=True, text=True)
                if str(pid) in result.stdout:
                    return False
            else:
                try:
                    os.kill(int(pid), 0)
                    return False
                except:
                    pass
        except:
            pass
    
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

def remove_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

def signal_handler(sig, frame):
    remove_lock()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ==================== ЛОГИ ====================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    ICONS = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'critical': '🔥',
        'database': '🗄️',
        'bot': '🤖',
        'user': '👤',
        'time': '⏱️'
    }

class ColoredFormatter(logging.Formatter):
    format_str = "%(asctime)s.%(msecs)03d"
    
    FORMATS = {
        logging.DEBUG: Colors.BLUE + format_str + " [🐛 DEBUG] %(message)s" + Colors.END,
        logging.INFO: Colors.GREEN + format_str + " [ℹ️ INFO] %(message)s" + Colors.END,
        logging.WARNING: Colors.YELLOW + format_str + " [⚠️ WARNING] %(message)s" + Colors.END,
        logging.ERROR: Colors.RED + format_str + " [❌ ERROR] %(message)s" + Colors.END,
        logging.CRITICAL: Colors.RED + Colors.BOLD + format_str + " [🔥 CRITICAL] %(message)s" + Colors.END,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ColoredFormatter())

log_file = LOG_DIR / f'bot_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# ==================== ЗАПУСК ====================

async def main():
    if not check_lock():
        logger.error("❌ Бот уже запущен!")
        sys.exit(1)
    
    try:
        print(Colors.CYAN + Colors.BOLD + """
╔══════════════════════════════════════════════════════════╗
║                    🐶 LEDOGE BOT v220226                 ║
║                 Автор: Stardamnplugg                     ║
╚══════════════════════════════════════════════════════════╝
""" + Colors.END)
        
        logger.info(f"{Colors.ICONS['database']} Инициализация базы данных...")
        start_time = time.time()
        init_db()
        logger.info(f"{Colors.ICONS['success']} База данных готова ({(time.time()-start_time)*1000:.1f}ms)")
        
        logger.info(f"{Colors.ICONS['bot']} Инициализация бота...")
        storage = MemoryStorage()
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher(storage=storage)
        
        dp.message.middleware(ThrottlingMiddleware(0.3))
        dp.callback_query.middleware(ThrottlingMiddleware(0.3))
        
        logger.info(f"{Colors.ICONS['info']} Регистрация хендлеров...")
        routers = [
            ("common", common.router),
            ("mining", mining.router),
            ("shop", shop.router),
            ("admin", admin.router),
            ("exchange", exchange.router),
            ("skinshop", skinshop.router),
            ("referral", referral.router),
            ("price_watch", price_watch.router),
        ]
        
        for name, router in routers:
            dp.include_router(router)
            logger.info(f"  {Colors.ICONS['success']} {name}.py загружен")
        
        bot_info = await bot.get_me()
        logger.info(f"{Colors.ICONS['bot']} Бот: @{bot_info.username} (ID: {bot_info.id})")
        logger.info(f"{Colors.ICONS['user']} Админ ID: {ADMIN_ID}")
        logger.info(f"{Colors.ICONS['database']} Логи сохраняются в: {LOG_DIR}")
        
        asyncio.create_task(update_prices())
        logger.info(f"{Colors.ICONS['success']} Фоновая задача волатильности запущена")
        
        from handlers.mining import clean_old_mining_records
        asyncio.create_task(clean_old_mining_records())
        logger.info(f"{Colors.ICONS['success']} Фоновая задача очистки майнинга запущена")
        
        print(Colors.GREEN + Colors.BOLD + """
╔══════════════════════════════════════════════════════════╗
║                    ✅ БОТ ГОТОВ К РАБОТЕ                 ║
╚══════════════════════════════════════════════════════════╝
""" + Colors.END)
        
        logger.info("⏳ Ожидание 5 секунд...")
        await asyncio.sleep(5)
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                logger.info("🚀 Запуск polling...")
                await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])
                break
            except TelegramConflictError:
                retry_count += 1
                logger.warning(f"⚠️ Конфликт ({retry_count}/{max_retries}), ждем 10 сек...")
                await asyncio.sleep(10)
                continue
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
                break
        
    except Exception as e:
        logger.critical(f"{Colors.ICONS['critical']} КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
    finally:
        remove_lock()
        logger.info(f"{Colors.ICONS['warning']} Бот остановлен")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{Colors.ICONS['warning']} Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"{Colors.ICONS['critical']} Непредвиденная ошибка: {e}", exc_info=True)
    finally:
        remove_lock()
