#!/usr/bin/env python3
"""Асинхронный скрипт для инициализации базы данных"""
import asyncio
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_database_async():
    """Асинхронная инициализация базы данных"""
    try:
        from database import db
        logger.info("Начинаем подключение к базе данных...")
        await db.connect()
        logger.info("✅ Подключение установлено, таблицы созданы/проверены!")
        await db.close()
        logger.info("✅ Инициализация базы данных завершена успешно!")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database_async())
    sys.exit(0 if success else 1)

