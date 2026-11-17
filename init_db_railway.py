#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для инициализации базы данных Railway"""
import asyncio
import sys
import logging
import os
import aiomysql
from dotenv import load_dotenv
import re

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_database_railway():
    """Инициализация БД с использованием параметров из .env (строки 16-17)"""
    try:
        # Парсим MYSQL_URL из .env
        mysql_url = os.getenv("MYSQL_URL")
        if not mysql_url:
            raise ValueError("MYSQL_URL не найден в переменных окружения")
        
        logger.info(f"MYSQL_URL найден: {mysql_url.split('@')[0]}@***")
        
        # Парсим URL
        regex = r"mysql:\/\/(.*?):(.*?)@(.*?):(\d+)\/(.*)"
        match = re.match(regex, mysql_url)
        if not match:
            raise ValueError("MYSQL_URL не соответствует формату mysql://user:pass@host:port/dbname")
        
        user, password, host, port, database = match.groups()
        port = int(port)
        
        # Если это внутренний адрес Railway, используем публичный адрес
        if 'railway.internal' in host:
            logger.warning(f"Обнаружен внутренний адрес Railway: {host}")
            logger.info("Используем публичный адрес Railway для локального подключения...")
            
            # Пробуем найти публичный адрес в переменных окружения (строки 16-17)
            # Или используем известный публичный адрес Railway
            public_host = os.getenv("MYSQL_PUBLIC_HOST") or os.getenv("RAILWAY_PUBLIC_HOST")
            public_port = os.getenv("MYSQL_PUBLIC_PORT") or os.getenv("RAILWAY_PUBLIC_PORT")
            
            if public_host and public_port:
                logger.info(f"Используем публичный адрес из переменных окружения: {public_host}:{public_port}")
                host = public_host
                port = int(public_port)
            else:
                # Используем известный публичный адрес Railway (из check_tables.py)
                # Это fallback, если публичный адрес не указан в переменных окружения
                logger.info("Публичный адрес не найден в переменных окружения")
                logger.info("Используем fallback адрес из check_tables.py (проверьте строки 16-17 в .env для актуального адреса)")
                
                # Используем значения из check_tables.py как fallback
                # ВАЖНО: Это временное решение. Для продакшена используйте переменные окружения
                fallback_host = 'turntable.proxy.rlwy.net'
                fallback_port = 11725
                
                logger.warning(f"Используем fallback адрес: {fallback_host}:{fallback_port}")
                logger.warning("Для продакшена добавьте MYSQL_PUBLIC_HOST и MYSQL_PUBLIC_PORT в .env (строки 16-17)")
                
                host = fallback_host
                port = fallback_port
        
        logger.info(f"Подключаемся к БД: {user}@{host}:{port}/{database}")
        
        # Подключаемся к БД
        connection = await aiomysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            charset='utf8mb4',
            connect_timeout=10
        )
        
        logger.info("Подключение установлено!")
        
        # Создаем таблицы
        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNSIGNED UNIQUE,
                    fio VARCHAR(255),
                    school VARCHAR(255),
                    class_number INT,
                    class_letter VARCHAR(10),
                    gender VARCHAR(10),
                    birth_year INT,
                    city VARCHAR(255),
                    language VARCHAR(20),
                    artifacts TEXT,
                    opened_profiles TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            'test_progress': """
                CREATE TABLE IF NOT EXISTS test_progress (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNSIGNED,
                    current_scene VARCHAR(255),
                    all_scenes TEXT,
                    profile_scores TEXT,
                    profession_scores TEXT,
                    lang VARCHAR(10),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            'test_results': """
                CREATE TABLE IF NOT EXISTS test_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNSIGNED,
                    finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    profile VARCHAR(255),
                    score INT,
                    details TEXT,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            'goals': """
                CREATE TABLE IF NOT EXISTS goals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNSIGNED,
                    title VARCHAR(255),
                    description TEXT,
                    deadline DATE,
                    priority INT,
                    progress INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        }
        
        async with connection.cursor() as cursor:
            for table_name, create_query in tables.items():
                try:
                    await cursor.execute(create_query)
                    logger.info(f"Таблица {table_name} проверена/создана")
                except Exception as e:
                    logger.error(f"Ошибка создания таблицы {table_name}: {e}")
                    raise
        
        connection.close()
        logger.info("Инициализация базы данных завершена успешно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database_railway())
    sys.exit(0 if success else 1)

