# ui_utils.py
"""
Утилиты для красивого интерфейса бота (оптимизировано для телефонов)
"""

def create_header(title, emoji="", width=40):
    """Создаёт простой заголовок"""
    return f"\n{emoji} <b>{title}</b> {emoji}\n" + "─" * 30

def create_section(title, emoji=""):
    """Создаёт заголовок секции"""
    return f"\n{emoji} <b>{title}</b>"

def create_subsection(title):
    """Создаёт подзаголовок"""
    return f"\n  ⚬ <b>{title}</b>"

def create_footer(width=40):
    """Создаёт подвал сообщения"""
    return "\n" + "─" * 30

def create_progress_bar(current, maximum, length=10, fill_char="█"):
    """Создаёт прогресс-бар"""
    if maximum == 0:
        filled = 0
    else:
        filled = int((current / maximum) * length)
    empty = length - filled
    bar = fill_char * filled + "░" * empty
    percentage = (current / maximum) * 100 if maximum > 0 else 0
    return f"{bar} {percentage:.1f}%"

def create_energy_bar(energy, max_energy, length=15):
    """Создаёт прогресс-бар для энергии"""
    return create_progress_bar(energy, max_energy, length, "█")

def format_number(num):
    """Форматирует большие числа"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.2f}"

def create_price_table(prices):
    """Создаёт таблицу с ценами (простая версия)"""
    lines = []
    lines.append("📈 <b>ТЕКУЩИЕ КУРСЫ</b>")
    lines.append("─" * 30)
    
    currency_names = {
        'bitkoin': '🪙 BitKoin',
        'ethireum': '⚡ Ethireum',
        'dodgecoin': '🐕 DodgeCoin',
        'tonkoin': '💎 TonKoin',
        'solanafast': '🌲 SolanaFast',
        'notcoine': '📱 NotCoine',
        'shibafloki': '🐶 ShibaFloki',
        'ledoge': '🐶 LEDOGE',
        'usdtoken': '💵 USDToken'
    }
    
    for code, price in prices.items():
        if code in currency_names:
            name = currency_names[code]
            lines.append(f"{name} — {price:.4f} $")
    
    lines.append("─" * 30)
    return "\n".join(lines)

def create_miner_list(miners, miners_data):
    """Создаёт отображение майнеров"""
    if not miners:
        return "   📭 У тебя пока нет майнеров"
    
    lines = []
    lines.append("⚙️ <b>ТВОИ МАЙНЕРЫ</b>")
    lines.append("─" * 30)
    
    for miner_type, quantity in miners.items():
        if quantity > 0 and miner_type in miners_data:
            miner = miners_data[miner_type]
            bonus = miner['bonus'] * 100
            # В miners_data уже есть эмодзи в названии, поэтому просто берем name
            lines.append(f"{miner['name']} — {quantity} шт.")
            lines.append(f"   ⬆️ +{bonus:.1f}% к шансу")
    
    lines.append("─" * 30)
    return "\n".join(lines)

def create_skin_shop_list(skins, owned_skins, current_skin):
    """Создаёт список скинов для магазина"""
    lines = []
    lines.append("👕 <b>МАГАЗИН СКИНОВ</b>")
    lines.append("─" * 30)
    
    for num, skin in enumerate(skins, 1):
        if skin[0] == 'developer':
            continue
        
        status = ""
        if skin[0] in owned_skins:
            status = "✅"
        if skin[0] == current_skin:
            status = "👑"
        
        price_str = f"{skin[3]} {skin[4].upper()}"
        lines.append(f"{num}. {skin[2]} {status}")
        lines.append(f"   💰 {price_str}")
        lines.append(f"   📝 {skin[6]}")
        lines.append("")
    
    lines.append("─" * 30)
    return "\n".join(lines)

def create_wardrobe_list(skins, owned_skins, current_skin):
    """Создаёт список скинов для шкафчика"""
    lines = []
    lines.append("👕 <b>ТВОЙ ШКАФЧИК</b>")
    lines.append("─" * 30)
    
    for num, skin in enumerate(skins, 1):
        if skin[0] in owned_skins:
            status = ""
            if skin[0] == current_skin:
                status = "👑 НАДЕТО"
            lines.append(f"{num}. {skin[2]} {status}")
            lines.append(f"   📝 {skin[6]}")
            lines.append("")
    
    lines.append("─" * 30)
    return "\n".join(lines)

def create_top_list(users, skins_data):
    """Создаёт топ пользователей (простая версия)"""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    lines = []
    lines.append("🏆 <b>ТОП МАЙНЕРОВ</b>")
    lines.append("─" * 30)
    
    for i, user in enumerate(users[:10]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user['first_name'] or user['username'] or f"User{user['user_id']}"
        name = name[:20] + "..." if len(name) > 20 else name
        
        # Скин пользователя - ВАЖНО: в skins_data уже есть эмодзи в названии
        skin_prefix = ""
        if user['skin'] != 'none' and user['skin'] in skins_data:
            skin_prefix = skins_data[user['skin']]['emoji'] + " "
        
        # Прогресс-бар
        max_balance = users[0]['ledoge']
        bar = create_progress_bar(user['ledoge'], max_balance, 8, "⭐")
        
        lines.append(f"{medal} {skin_prefix}{name}")
        lines.append(f"   {bar} {format_number(user['ledoge'])} 🐶")
        lines.append("")
    
    lines.append("─" * 30)
    return "\n".join(lines)

def create_booster_info(booster, balance):
    """Создаёт информацию о бустерах"""
    lines = []
    lines.append("✨ <b>МАГАЗИН БУСТЕРОВ</b>")
    lines.append("─" * 30)
    
    lines.append(f"💰 Баланс: {format_number(balance)} 🐶")
    lines.append(f"✨ Множитель: x{booster['multiplier']}")
    
    if booster['expiry']:
        from datetime import datetime
        time_left = booster['expiry'] - datetime.now()
        minutes = int(time_left.seconds / 60)
        lines.append(f"⏳ Осталось: {minutes} мин")
    
    lines.append("─" * 30)
    return "\n".join(lines)

def create_wallet_info(balances, miners, miners_data, owned_skins, skins_data, current_skin):
    """Создаёт информацию о кошельке (простая версия)"""
    lines = []
    lines.append("💰 <b>КРИПТОКОШЕЛЁК</b>")
    lines.append("─" * 30)
    
    # Активы
    lines.append("📊 <b>АКТИВЫ</b>")
    for name, balance in balances.items():
        if balance > 0 or 'LEDOGE' in name or 'USDToken' in name:
            formatted = format_number(balance)
            lines.append(f"{name} — {formatted}")
    
    # Майнеры - ИСПРАВЛЕНО!
    if miners:
        lines.append("")
        lines.append("⚙️ <b>МАЙНЕРЫ</b>")
        for miner_type, quantity in miners.items():
            if quantity > 0 and miner_type in miners_data:
                miner = miners_data[miner_type]
                # В miners_data уже есть эмодзи в названии, поэтому просто берем name
                lines.append(f"{miner['name']} — {quantity} шт.")
    
    # Скины - ИСПРАВЛЕНО!
    if owned_skins:
        lines.append("")
        lines.append("👕 <b>СКИНЫ</b>")
        for skin_key in owned_skins[:3]:
            if skin_key in skins_data:
                skin = skins_data[skin_key]
                # В skins_data уже есть эмодзи в названии, поэтому просто берем name
                lines.append(f"{skin['name']}")
        if len(owned_skins) > 3:
            lines.append(f"... и ещё {len(owned_skins)-3} скинов")
    
    # Текущий скин - ИСПРАВЛЕНО!
    if current_skin != 'none' and current_skin in skins_data:
        lines.append("")
        lines.append(f"👑 <b>НАДЕТО:</b> {skins_data[current_skin]['name']}")
    
    lines.append("─" * 30)
    return "\n".join(lines)