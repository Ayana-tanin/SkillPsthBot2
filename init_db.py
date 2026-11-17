#!/usr/bin/env python3
"""Скрипт для инициализации базы данных"""
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from api.db import init_database
    logger.info("Начинаем инициализацию базы данных...")
    init_database()
    logger.info("✅ Инициализация базы данных завершена успешно!")
except Exception as e:
    logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
    sys.exit(1)

