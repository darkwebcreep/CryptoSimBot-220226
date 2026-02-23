# handlers/mining.py
import asyncio
import random
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user, get_balance, update_balance,
    get_user_energy, use_energy, get_user_booster, set_user_booster,
    add_max_energy, get_user_miners, buy_miner, get_miner_bonus
)
from keyboards import mining_menu, tap_menu, main_menu, boosters_menu, miners_menu
from config import CURRENCIES, ADMIN_ID, TAP_BOOSTERS, ENERGY_BOOSTERS, MINERS, CHANNEL_LINK, SUPPORT_LINK
from ui_utils import create_header, create_section, create_footer

logger = logging.getLogger(__name__)

router = Router()

class MiningStates(StatesGroup):
    mining_in_progress = State()
    confirm_restart = State()

# ==================== ТЕКСТОВЫЙ ПРОГРЕСС-БАР ====================
def create_text_progress(current, total, length=10):
    """Создаёт текстовый прогресс-бар с символами █ и ░"""
    filled = int((current / total) * length)
    empty = length - filled
    return "█" * filled + "░" * empty

# ==================== ЗАЩИТА ОТ ДДОС ====================
last_mining_time = {}

def can_start_mining(user_id):
    """Проверяет, можно ли начать майнинг"""
    if user_id in last_mining_time:
        last_time = last_mining_time[user_id]
        if datetime.now() - last_time < timedelta(seconds=10):
            return False, int(10 - (datetime.now() - last_time).seconds)
    return True, 0

async def clean_old_mining_records():
    """Очищает старые записи о майнинге"""
    while True:
        await asyncio.sleep(3600)
        now = datetime.now()
        to_delete = []
        for user_id, last_time in last_mining_time.items():
            if now - last_time > timedelta(minutes=5):
                to_delete.append(user_id)
        for user_id in to_delete:
            del last_mining_time[user_id]
        logger.debug(f"🧹 Очищено {len(to_delete)} старых записей майнинга")

# ==================== МАЙНИНГ ====================

@router.message(F.text == "⛏ Майнинг")
async def show_mining_menu(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    logger.info(f"⛏ Пользователь {username} (ID: {user_id}) открыл меню майнинга")
    
    text = (
        "⛏ <b>МАЙНИНГ КРИПТОВАЛЮТ</b>\n\n"
        "Выбери монету для майнинга:\n\n"
        "🪙 <b>BitKoin</b> — сложный майнинг\n"
        "   Шанс: 1% | Время: 10 сек\n\n"
        "⚡ <b>Ethireum</b> — средний майнинг\n"
        "   Шанс: 3% | Время: 5 сек\n\n"
        "🐕 <b>DodgeCoin</b> — легкий майнинг\n"
        "   Шанс: 10% | Время: 3 сек\n\n"
        "💎 <b>TonKoin</b> — средний майнинг\n"
        "   Шанс: 5% | Время: 4 сек\n\n"
        "🌲 <b>SolanaFast</b> — быстрый майнинг\n"
        "   Шанс: 2% | Время: 2 сек\n\n"
        "⚙️ <b>Майнеры</b> — увеличь шанс майнинга"
    )
    
    await message.answer(text, reply_markup=mining_menu())

# ==================== МАЙНЕРЫ ====================

@router.message(F.text == "⚙️ Майнеры")
async def show_miners(message: Message):
    user_id = message.from_user.id
    balance = get_balance(user_id, 'ledoge')
    user_miners = get_user_miners(user_id)
    
    text = "⚙️ <b>МАГАЗИН МАЙНЕРОВ</b>\n\n"
    text += f"💰 Твой баланс: {balance:.2f} LEDOGE\n"
    text += "Майнеры увеличивают шанс успешного майнинга!\n\n"
    text += "🎯 <b>Доступные майнеры:</b>\n\n"
    
    for key, miner in MINERS.items():
        owned = user_miners.get(key, 0)
        bonus_percent = miner['bonus'] * 100
        text += f"{miner['emoji']} <b>{miner['name']}</b>\n"
        text += f"   💰 Цена: {miner['price']} LEDOGE\n"
        text += f"   ⬆️ Бонус: +{bonus_percent}% к шансу\n"
        text += f"   📝 {miner['description']}\n"
        text += f"   📊 У тебя: {owned} шт.\n\n"
    
    await message.answer(text, reply_markup=miners_menu())

# ==================== ТАПАЛКА ====================

@router.message(F.text == "☝ Тапалка")
async def show_tap_menu(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    try:
        energy, max_energy = get_user_energy(user_id)
        booster = get_user_booster(user_id)
        
        logger.info(f"☝ {username} открыл тапалку, энергия: {energy}/{max_energy}, множитель: {booster['multiplier']}x")
        
        text = create_header("ТАПАЛКА", "☝️") + "\n\n"
        
        energy_bar = create_text_progress(energy, max_energy, 15)
        text += f"⚡ <b>ЭНЕРГИЯ</b>\n"
        text += f"[{energy_bar}] {energy}/{max_energy}\n\n"
        
        text += f"✨ <b>МНОЖИТЕЛЬ</b>: x{booster['multiplier']}\n"
        if booster['expiry']:
            time_left = booster['expiry'] - datetime.now()
            minutes = int(time_left.seconds / 60)
            text += f"⏳ Осталось: {minutes} мин\n"
        
        text += "\n" + create_section("МОНЕТЫ", "🎯") + "\n"
        text += "• 📱 NotCoine — 1-5 за тап\n"
        text += "• 🐶 ShibaFloki — 1-3 за тап\n"
        
        text += create_footer()
        
        await message.answer(text, reply_markup=tap_menu())
        
    except Exception as e:
        logger.error(f"❌ Ошибка в show_tap_menu: {e}")
        await message.answer("❌ Произошла ошибка. Попробуй позже.")

# ==================== БУСТЕРЫ ====================

@router.message(F.text == "✨ Бустеры")
async def show_boosters(message: Message):
    user_id = message.from_user.id
    balance = get_balance(user_id, 'ledoge')
    booster = get_user_booster(user_id)
    
    text = "✨ <b>МАГАЗИН БУСТЕРОВ</b>\n\n"
    text += f"💰 Твой баланс: {balance:.2f} LEDOGE\n"
    text += f"📊 Текущий множитель: {booster['multiplier']}x\n\n"
    text += "🎯 <b>Множители монет (1 час):</b>\n"
    
    for key, booster_info in TAP_BOOSTERS.items():
        text += f"• {booster_info['name']} — {booster_info['price']} LEDOGE\n"
    
    text += "\n🔋 <b>Увеличение энергии (навсегда):</b>\n"
    for key, booster_info in ENERGY_BOOSTERS.items():
        text += f"• {booster_info['name']} +{booster_info['energy']} — {booster_info['price']} LEDOGE\n"
    
    await message.answer(text, reply_markup=boosters_menu())

# ==================== ОСНОВНАЯ ФУНКЦИЯ МАЙНИНГА ====================

async def start_mining_process(message: Message, state: FSMContext, coin_name: str, base_chance: float, reward: float, wait_time: int, currency: str, username: str, user_id: int):
    """Основной процесс майнинга"""
    bonus_multiplier = get_miner_bonus(user_id)
    final_chance = min(base_chance * bonus_multiplier, 0.95)
    
    logger.info(f"⛏ {username} начал майнинг {coin_name}")
    logger.info(f"📊 Базовый шанс: {base_chance*100}%, Бонус: x{bonus_multiplier:.2f}, Итог: {final_chance*100:.1f}%")
    
    try:
        await state.set_state(MiningStates.mining_in_progress)
        
        bonus_text = ""
        if bonus_multiplier > 1.0:
            bonus_text = f"\n✨ Бонус от майнеров: x{bonus_multiplier:.2f} к шансу"
        
        progress_msg = await message.answer(
            f"🪙 <b>Майнинг {coin_name} запущен...</b>\n\n"
            f"⏱ Время: {wait_time} сек\n"
            f"📊 Базовый шанс: {base_chance*100}%{bonus_text}\n"
            f"🎯 Итоговый шанс: {final_chance*100:.1f}%\n\n"
            f"⏳ Прогресс: [░░░░░░░░░░] 0%\n\n"
            f"<i>Идет поиск блока...</i>"
        )
        
        mining_completed = True
        for i in range(1, wait_time + 1):
            current_state = await state.get_state()
            if current_state != MiningStates.mining_in_progress:
                mining_completed = False
                break
                
            await asyncio.sleep(1)
            
            progress_bar = create_text_progress(i, wait_time, 10)
            percent = int((i / wait_time) * 100)
            
            try:
                await progress_msg.edit_text(
                    f"🪙 <b>Майнинг {coin_name}...</b>\n\n"
                    f"⏱ Прогресс: [{progress_bar}] {percent}%\n"
                    f"📊 Шанс успеха: {final_chance*100:.1f}%\n\n"
                    f"<i>Осталось {wait_time - i} сек...</i>"
                )
            except:
                pass
            
            if i % 2 == 0:
                logger.debug(f"⛏ {username} майнит... {i}/{wait_time} сек")
        
        if mining_completed:
            if random.random() < final_chance:
                update_balance(user_id, currency, reward, 'add')
                new_balance = get_balance(user_id, currency)
                logger.info(f"⛏ ✅ {username} УСПЕХ! Получено {reward} {currency}")
                
                if isinstance(new_balance, float) and new_balance < 0.001:
                    result_text = (
                        f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n"
                        f"Ты намайнил: {reward:.8f} {currency}\n"
                        f"💰 Баланс: {new_balance:.8f} {currency}"
                    )
                else:
                    result_text = (
                        f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n"
                        f"Ты намайнил: {reward:.2f} {currency}\n"
                        f"💰 Баланс: {new_balance:.2f} {currency}"
                    )
            else:
                consolation = random.randint(1, 3)
                update_balance(user_id, 'ledoge', consolation, 'add')
                new_balance = get_balance(user_id, 'ledoge')
                logger.info(f"⛏ ❌ {username} НЕУДАЧА. +{consolation} LEDOGE")
                
                result_text = (
                    f"😢 <b>Неудача</b>\n\n"
                    f"Блок не найден...\n"
                    f"Но за старание: +{consolation} LEDOGE\n"
                    f"💰 LEDOGE: {new_balance:.2f}"
                )
            
            try:
                await progress_msg.edit_text(result_text)
            except:
                await message.answer(result_text)
        
    except Exception as e:
        logger.error(f"⛏ ОШИБКА для {username}: {e}")
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()

async def start_mining(message: Message, state: FSMContext, coin_name: str, base_chance: float, reward: float, wait_time: int, currency: str):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Проверяем тайм-аут
    can_start, wait_time_left = can_start_mining(user_id)
    if not can_start:
        await message.answer(f"⏳ Подожди еще {wait_time_left} секунд перед новым майнингом")
        return
    
    # Проверяем, не майнит ли уже
    current_state = await state.get_state()
    if current_state:
        kb = [
            [KeyboardButton(text="✅ Да, прервать")],
            [KeyboardButton(text="❌ Нет, продолжать")]
        ]
        markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        
        await message.answer(
            "⏳ Ты уже майнишь! Хочешь прервать текущий майнинг и начать новый?",
            reply_markup=markup
        )
        await state.update_data(
            new_mining={
                'coin_name': coin_name,
                'base_chance': base_chance,
                'reward': reward,
                'wait_time': wait_time,
                'currency': currency
            }
        )
        await state.set_state(MiningStates.confirm_restart)
        return
    
    last_mining_time[user_id] = datetime.now()
    await start_mining_process(message, state, coin_name, base_chance, reward, wait_time, currency, username, user_id)

@router.message(MiningStates.confirm_restart)
async def process_restart_confirm(message: Message, state: FSMContext):
    """Обрабатывает подтверждение перезапуска майнинга"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    if message.text == "✅ Да, прервать":
        data = await state.get_data()
        new_mining = data.get('new_mining')
        
        if new_mining:
            await state.clear()
            last_mining_time[user_id] = datetime.now()
            await start_mining_process(
                message, state,
                new_mining['coin_name'],
                new_mining['base_chance'],
                new_mining['reward'],
                new_mining['wait_time'],
                new_mining['currency'],
                username, user_id
            )
        else:
            await state.clear()
            await message.answer("❌ Ошибка при перезапуске. Попробуй снова.")
    
    elif message.text == "❌ Нет, продолжать":
        await state.clear()
        await message.answer("✅ Продолжай текущий майнинг!")
    
    else:
        await message.answer("❌ Используй кнопки Да или Нет")

# ==================== ОБРАБОТЧИКИ МАЙНИНГА ====================

@router.message(F.text == "🪙 Майнить BitKoin (сложно)")
async def mine_bitcoin(message: Message, state: FSMContext):
    await start_mining(message, state, "BitKoin", 0.01, 0.00000001, 10, "bitkoin")

@router.message(F.text == "⚡ Майнить Ethireum")
async def mine_ethireum(message: Message, state: FSMContext):
    await start_mining(message, state, "Ethireum", 0.03, 0.0001, 5, "ethireum")

@router.message(F.text == "🐕 Майнить DodgeCoin")
async def mine_dodgecoin(message: Message, state: FSMContext):
    await start_mining(message, state, "DodgeCoin", 0.10, 1, 3, "dodgecoin")

@router.message(F.text == "💎 Майнить TonKoin")
async def mine_tonkoin(message: Message, state: FSMContext):
    await start_mining(message, state, "TonKoin", 0.05, 0.5, 4, "tonkoin")

@router.message(F.text == "🌲 Майнить SolanaFast")
async def mine_solana(message: Message, state: FSMContext):
    await start_mining(message, state, "SolanaFast", 0.02, 0.01, 2, "solanafast")

# ==================== ОБРАБОТЧИКИ ТАПАЛКИ ====================

@router.message(F.text == "📱 Тапать NotCoine")
async def tap_notcoin(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    success, energy = use_energy(user_id)
    if not success:
        energy, max_energy = get_user_energy(user_id)
        await message.answer(f"😴 Нет энергии! Текущая: {energy}/{max_energy}")
        return
    
    booster = get_user_booster(user_id)
    reward = round(random.uniform(1, 5) * booster['multiplier'], 2)
    update_balance(user_id, 'notcoine', reward, 'add')
    
    total = get_balance(user_id, 'notcoine')
    energy, max_energy = get_user_energy(user_id)
    
    logger.info(f"📱 {username} натапал {reward} NotCoine (x{booster['multiplier']})")
    
    await message.answer(
        f"📱 <b>+{reward} NotCoine!</b> (x{booster['multiplier']})\n"
        f"⚡ Энергия: {energy}/{max_energy}\n"
        f"💰 Всего: {total:.2f}"
    )

@router.message(F.text == "🐶 Тапать ShibaFloki")
async def tap_shiba(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    success, energy = use_energy(user_id)
    if not success:
        energy, max_energy = get_user_energy(user_id)
        await message.answer(f"😴 Нет энергии! Текущая: {energy}/{max_energy}")
        return
    
    booster = get_user_booster(user_id)
    reward = round(random.uniform(1, 3) * booster['multiplier'], 2)
    update_balance(user_id, 'shibafloki', reward, 'add')
    
    total = get_balance(user_id, 'shibafloki')
    energy, max_energy = get_user_energy(user_id)
    
    logger.info(f"🐶 {username} натапал {reward} ShibaFloki (x{booster['multiplier']})")
    
    await message.answer(
        f"🐶 <b>+{reward} ShibaFloki!</b> (x{booster['multiplier']})\n"
        f"⚡ Энергия: {energy}/{max_energy}\n"
        f"💰 Всего: {total:.2f}"
    )

# ==================== ОБРАБОТЧИКИ БУСТЕРОВ ====================

@router.message(F.text.startswith("✨ x2"))
async def buy_x2_booster(message: Message):
    user_id = message.from_user.id
    price = TAP_BOOSTERS['x2']['price']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    set_user_booster(user_id, 2, 3600)
    await message.answer("✅ Бустер x2 активирован на 1 час!")

@router.message(F.text.startswith("🔥 x3"))
async def buy_x3_booster(message: Message):
    user_id = message.from_user.id
    price = TAP_BOOSTERS['x3']['price']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    set_user_booster(user_id, 3, 3600)
    await message.answer("✅ Бустер x3 активирован на 1 час!")

@router.message(F.text.startswith("⚡ x4"))
async def buy_x4_booster(message: Message):
    user_id = message.from_user.id
    price = TAP_BOOSTERS['x4']['price']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    set_user_booster(user_id, 4, 3600)
    await message.answer("✅ Бустер x4 активирован на 1 час!")

@router.message(F.text.startswith("💎 x5"))
async def buy_x5_booster(message: Message):
    user_id = message.from_user.id
    price = TAP_BOOSTERS['x5']['price']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    set_user_booster(user_id, 5, 3600)
    await message.answer("✅ Бустер x5 активирован на 1 час!")

@router.message(F.text.startswith("🔋 Малая"))
async def buy_small_energy(message: Message):
    user_id = message.from_user.id
    price = ENERGY_BOOSTERS['small']['price']
    energy = ENERGY_BOOSTERS['small']['energy']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    add_max_energy(user_id, energy)
    await message.answer(f"✅ Максимальная энергия +{energy}!")

@router.message(F.text.startswith("⚡ Средняя"))
async def buy_medium_energy(message: Message):
    user_id = message.from_user.id
    price = ENERGY_BOOSTERS['medium']['price']
    energy = ENERGY_BOOSTERS['medium']['energy']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    add_max_energy(user_id, energy)
    await message.answer(f"✅ Максимальная энергия +{energy}!")

@router.message(F.text.startswith("💪 Большая"))
async def buy_large_energy(message: Message):
    user_id = message.from_user.id
    price = ENERGY_BOOSTERS['large']['price']
    energy = ENERGY_BOOSTERS['large']['energy']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    add_max_energy(user_id, energy)
    await message.answer(f"✅ Максимальная энергия +{energy}!")

@router.message(F.text.startswith("🚀 Максимальная"))
async def buy_max_energy(message: Message):
    user_id = message.from_user.id
    price = ENERGY_BOOSTERS['max']['price']
    energy = ENERGY_BOOSTERS['max']['energy']
    
    if get_balance(user_id, 'ledoge') < price:
        await message.answer(f"❌ Недостаточно LEDOGE! Нужно: {price}")
        return
    
    update_balance(user_id, 'ledoge', price, 'subtract')
    add_max_energy(user_id, energy)
    await message.answer(f"✅ Максимальная энергия +{energy}!")

# ==================== ОБРАБОТЧИКИ МАЙНЕРОВ ====================

@router.message(F.text.startswith("🔌 USB"))
async def buy_usb_miner(message: Message):
    user_id = message.from_user.id
    miner = MINERS['usb']
    
    success, msg = buy_miner(user_id, 'usb', miner['price'])
    await message.answer(msg)
    if success:
        bonus = miner['bonus'] * 100
        await message.answer(f"✅ Шанс майнинга +{bonus}%!")

@router.message(F.text.startswith("📱 Смартфон"))
async def buy_smartphone_miner(message: Message):
    user_id = message.from_user.id
    miner = MINERS['smartphone']
    
    success, msg = buy_miner(user_id, 'smartphone', miner['price'])
    await message.answer(msg)
    if success:
        bonus = miner['bonus'] * 100
        await message.answer(f"✅ Шанс майнинга +{bonus}%!")

@router.message(F.text.startswith("🔷 FPGA"))
async def buy_fpga_miner(message: Message):
    user_id = message.from_user.id
    miner = MINERS['fpga']
    
    success, msg = buy_miner(user_id, 'fpga', miner['price'])
    await message.answer(msg)
    if success:
        bonus = miner['bonus'] * 100
        await message.answer(f"✅ Шанс майнинга +{bonus}%!")

@router.message(F.text.startswith("🖥️ CPU"))
async def buy_cpu_miner(message: Message):
    user_id = message.from_user.id
    miner = MINERS['cpu']
    
    success, msg = buy_miner(user_id, 'cpu', miner['price'])
    await message.answer(msg)
    if success:
        bonus = miner['bonus'] * 100
        await message.answer(f"✅ Шанс майнинга +{bonus}%!")

@router.message(F.text.startswith("🎮 GPU"))
async def buy_gpu_miner(message: Message):
    user_id = message.from_user.id
    miner = MINERS['gpu']
    
    success, msg = buy_miner(user_id, 'gpu', miner['price'])
    await message.answer(msg)
    if success:
        bonus = miner['bonus'] * 100
        await message.answer(f"✅ Шанс майнинга +{bonus}%!")

@router.message(F.text.startswith("⚙️ ASIC"))
async def buy_asic_miner(message: Message):
    user_id = message.from_user.id
    miner = MINERS['asic']
    
    success, msg = buy_miner(user_id, 'asic', miner['price'])
    await message.answer(msg)
    if success:
        bonus = miner['bonus'] * 100
        await message.answer(f"✅ Шанс майнинга +{bonus}%!")

# ==================== ССЫЛКИ ====================

@router.message(F.text == "🔗 Канал и поддержка")
async def show_links(message: Message):
    await message.answer(
        "🔗 <b>Полезные ссылки:</b>\n\n"
        f"📢 <b>Наш канал:</b> {CHANNEL_LINK}\n"
        f"🆕 Все новости и обновления там!\n\n"
        f"🆘 <b>Поддержка:</b> {SUPPORT_LINK}\n"
        f"📝 Пиши если нашел баг или есть вопросы\n\n"
        f"👑 <b>Создатель:</b> @woolfcreep"
    )

# ==================== НАЗАД ====================

@router.message(F.text == "◀ Назад в меню")
async def back_to_main(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    logger.info(f"◀ {username} вернулся в главное меню")
    
    # Очищаем состояние при выходе в меню
    await state.clear()
    
    if user_id == ADMIN_ID:
        from keyboards import admin_keyboard
        await message.answer("🔧 Админ-меню:", reply_markup=admin_keyboard())
    else:
        await message.answer("Главное меню:", reply_markup=main_menu())

async def clean_old_mining_records():
    """Очищает старые записи о майнинге"""
    from datetime import datetime, timedelta
    global last_mining_time
    
    while True:
        await asyncio.sleep(3600)  # Каждый час
        now = datetime.now()
        to_delete = []
        for user_id, last_time in last_mining_time.items():
            if now - last_time > timedelta(minutes=5):
                to_delete.append(user_id)
        for user_id in to_delete:
            del last_mining_time[user_id]
        logger.info(f"🧹 Очищено {len(to_delete)} старых записей майнинга")
