#!/usr/bin/env python3
"""Скрипт для проверки переменных окружения БД"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Проверка переменных окружения для БД:")
print("=" * 60)

# Проверяем MYSQL_URL
mysql_url = os.getenv("MYSQL_URL")
if mysql_url:
    print(f"\nMYSQL_URL: {mysql_url}")
    # Маскируем пароль
    if "@" in mysql_url:
        parts = mysql_url.split("@")
        if len(parts) > 1:
            masked = parts[0].split(":")[0] + ":***@" + parts[1]
            print(f"MYSQL_URL (маскированный): {masked}")
else:
    print("\nMYSQL_URL: не установлен")

# Проверяем отдельные переменные
print("\nОтдельные переменные MySQL:")
print(f"MYSQLHOST: {os.getenv('MYSQLHOST', 'не установлен')}")
print(f"MYSQL_HOST: {os.getenv('MYSQL_HOST', 'не установлен')}")
print(f"MYSQLPORT: {os.getenv('MYSQLPORT', 'не установлен')}")
print(f"MYSQL_PORT: {os.getenv('MYSQL_PORT', 'не установлен')}")
print(f"MYSQLUSER: {os.getenv('MYSQLUSER', 'не установлен')}")
print(f"MYSQL_USER: {os.getenv('MYSQL_USER', 'не установлен')}")
print(f"MYSQLPASSWORD: {'***' if os.getenv('MYSQLPASSWORD') else 'не установлен'}")
print(f"MYSQL_PASSWORD: {'***' if os.getenv('MYSQL_PASSWORD') else 'не установлен'}")
print(f"MYSQLDATABASE: {os.getenv('MYSQLDATABASE', 'не установлен')}")
print(f"MYSQL_DATABASE: {os.getenv('MYSQL_DATABASE', 'не установлен')}")

print("\n" + "=" * 60)
print("💡 Если используется внутренний адрес Railway (mysql.railway.internal),")
print("   его нужно заменить на публичный адрес для локального подключения.")
print("=" * 60)

