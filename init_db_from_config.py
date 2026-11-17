#!/usr/bin/env python3
"""Скрипт для инициализации базы данных с использованием параметров из config.py"""
import asyncio
import sys
import logging
import aiomysql

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_database_from_config():
    """Инициализация БД с использованием параметров из config.py"""
    try:
        from config import settings
        
        # Используем параметры из config.py
        host = settings.MYSQL_HOST
        port = settings.MYSQL_PORT
        user = settings.MYSQL_USER
        password = settings.MYSQL_PASSWORD
        database = settings.MYSQL_DATABASE
        
        logger.info(f"Подключаемся к БД: {user}@{host}:{port}/{database}")
        
        # Подключаемся к БД
        connection = await aiomysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            charset='utf8mb4'
        )
        
        logger.info("✅ Подключение установлено!")
        
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
                    logger.info(f"✅ Таблица {table_name} проверена/создана")
                except Exception as e:
                    logger.error(f"❌ Ошибка создания таблицы {table_name}: {e}")
                    raise
        
        connection.close()
        logger.info("✅ Инициализация базы данных завершена успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database_from_config())
    sys.exit(0 if success else 1)

