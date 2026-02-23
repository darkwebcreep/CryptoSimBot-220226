# update_database.py
import sqlite3
import json

DB_NAME = 'crypto_sim.db'

print("🔄 Обновление базы данных...")

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Добавляем колонку owned_skins в таблицу users
try:
    cur.execute("ALTER TABLE users ADD COLUMN owned_skins TEXT DEFAULT '[]'")
    print("✅ Колонка owned_skins добавлена")
except sqlite3.OperationalError:
    print("ℹ️ Колонка owned_skins уже существует")

# Проверяем структуру таблицы
cur.execute("PRAGMA table_info(users)")
columns = cur.fetchall()
print("\n📊 Текущая структура таблицы users:")
for col in columns:
    print(f"   {col[1]} - {col[2]}")

conn.commit()
conn.close()

print("\n✅ База данных обновлена!")