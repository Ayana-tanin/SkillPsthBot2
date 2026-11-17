#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для создания базы данных на основе параметров из .env (строки 16-17)"""
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

async def create_database():
    """Создание БД с использованием параметров из .env"""
    try:
        # Парсим MYSQL_URL из .env
        mysql_url = os.getenv("MYSQL_URL")
        if not mysql_url:
            raise ValueError("MYSQL_URL не найден в переменных окружения")
        
        logger.info("MYSQL_URL найден в .env")
        
        # Парсим URL
        regex = r"mysql:\/\/(.*?):(.*?)@(.*?):(\d+)\/(.*)"
        match = re.match(regex, mysql_url)
        if not match:
            raise ValueError("MYSQL_URL не соответствует формату mysql://user:pass@host:port/dbname")
        
        user, password, host, port, database = match.groups()
        port = int(port)
        
        logger.info(f"Параметры подключения: user={user}, host={host}, port={port}, database={database}")
        
        # Если это внутренний адрес Railway, предупреждаем
        if 'railway.internal' in host:
            logger.warning("=" * 60)
            logger.warning("ВНИМАНИЕ: Обнаружен внутренний адрес Railway!")
            logger.warning("Для локального подключения нужен публичный адрес.")
            logger.warning("Проверьте строки 16-17 в .env файле.")
            logger.warning("Если публичный адрес указан в строках 16-17, скрипт попытается его использовать.")
            logger.warning("=" * 60)
            
            # Пробуем найти публичный адрес в переменных окружения (строки 16-17)
            # Проверяем различные варианты названий переменных
            public_host = (
                os.getenv("MYSQL_PUBLIC_HOST") or 
                os.getenv("RAILWAY_PUBLIC_HOST") or
                os.getenv("MYSQLHOST") or
                os.getenv("MYSQL_HOST")
            )
            public_port = (
                os.getenv("MYSQL_PUBLIC_PORT") or 
                os.getenv("RAILWAY_PUBLIC_PORT") or
                os.getenv("MYSQLPORT") or
                os.getenv("MYSQL_PORT")
            )
            
            if public_host and public_port:
                logger.info(f"Найден публичный адрес: {public_host}:{public_port}")
                host = public_host
                port = int(public_port)
            else:
                logger.error("Публичный адрес не найден в переменных окружения!")
                logger.error("Для локального подключения добавьте в .env (строки 16-17):")
                logger.error("  MYSQL_PUBLIC_HOST=ваш_публичный_хост")
                logger.error("  MYSQL_PUBLIC_PORT=ваш_публичный_порт")
                logger.error("")
                logger.error("Или запустите скрипт на сервере Railway, где внутренний адрес доступен.")
                raise ConnectionError("Публичный адрес Railway не найден. Проверьте строки 16-17 в .env")
        
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
        logger.info("=" * 60)
        logger.info("Инициализация базы данных завершена успешно!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_database())
    sys.exit(0 if success else 1)

