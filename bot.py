import logging
import os
import asyncio
import signal
import subprocess
import sys
import time
import threading
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from database import db, UserManager, TestProgressManager, TestResultsManager

# Импорт обработчиков
from handlers import commands, callbacks, messages, goals, materials, test, registration
from config import settings

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Создаем отдельный логгер для FastAPI
fastapi_logger = logging.getLogger('fastapi')
fastapi_logger.setLevel(logging.INFO)
fastapi_handler = logging.StreamHandler()
fastapi_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
fastapi_logger.addHandler(fastapi_handler)

# Инициализация бота и диспетчера
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Flag to track if shutdown is in progress
is_shutting_down = False

def wait_for_tables(cursor, expected_tables, max_retries=30, retry_interval=1):
    """Ожидание создания всех таблиц."""
    for i in range(max_retries):
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        missing_tables = set(expected_tables) - set(tables)
        
        if not missing_tables:
            logger.info(f"Все таблицы созданы: {', '.join(tables)}")
            return True
            
        logger.info(f"Ожидание создания таблиц... (попытка {i+1}/{max_retries})")
        logger.info(f"Ожидаемые таблицы: {', '.join(expected_tables)}")
        logger.info(f"Найденные таблицы: {', '.join(tables)}")
        logger.info(f"Отсутствующие таблицы: {', '.join(missing_tables)}")
        time.sleep(retry_interval)
    
    logger.error(f"Не все таблицы созданы за отведенное время. Ожидались: {', '.join(expected_tables)}")
    return False

def run_fastapi():
    """Запуск FastAPI в отдельном процессе."""
    try:
        logger.info("Запуск FastAPI приложения...")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", str(settings.PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Вывод логов FastAPI через отдельный логгер
        def log_output(pipe, log_func):
            for line in pipe:
                if line.strip():
                    # Убираем префикс INFO: из логов FastAPI
                    line = line.replace("INFO:     ", "").strip()
                    log_func(line)
        
        threading.Thread(target=log_output, args=(process.stdout, fastapi_logger.info), daemon=True).start()
        threading.Thread(target=log_output, args=(process.stderr, fastapi_logger.error), daemon=True).start()
        
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске FastAPI: {e}")
        raise

# Регистрация обработчиков
def register_handlers(dispatcher):
    try:
        logger.info("Регистрация обработчиков...")
        commands.register_handlers(dispatcher)
        callbacks.register_handlers(dispatcher)
        goals.register_handlers(dispatcher)
        materials.register_handlers(dispatcher)
        test.register_handlers(dispatcher)
        registration.register_registration_handlers(dispatcher)
        messages.register_handlers(dispatcher)
        logger.info("Обработчики успешно зарегистрированы")
    except Exception as e:
        logger.error(f"Ошибка при регистрации обработчиков: {e}")
        raise

async def on_startup():
    """Действия при запуске бота"""
    try:
        # Запускаем FastAPI
        api_process = run_fastapi()
        
        # Даем время на запуск FastAPI
        await asyncio.sleep(2)
        
        # Подключение к базе данных
        await db.connect()
        logger.info("✅ База данных подключена")
        
        # Проверяем создание таблиц
        try:
            async with db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Список ожидаемых таблиц
                    expected_tables = ['users', 'test_results', 'test_progress', 'goals', 'materials', 'notes']
                    
                    # Проверяем наличие таблиц
                    await cursor.execute("SHOW TABLES")
                    tables = [table[0] for table in await cursor.fetchall()]
                    missing_tables = set(expected_tables) - set(tables)
                    
                    if missing_tables:
                        logger.error(f"Отсутствующие таблицы: {', '.join(missing_tables)}")
                        raise Exception("Не все таблицы были созданы")
                    
                    logger.info(f"✅ Все таблицы проверены: {', '.join(tables)}")
                    
        except Exception as e:
            logger.error(f"Ошибка при проверке базы данных: {e}")
            raise
        
        # Регистрация обработчиков
        register_handlers(dp)
        logger.info("✅ Обработчики зарегистрированы")
        
        # Удаление вебхука (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Вебхук удален")
        
        logger.info("🚀 Бот успешно запущен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
        raise

async def on_shutdown():
    """Действия при остановке бота"""
    global is_shutting_down
    if is_shutting_down:
        return
    
    is_shutting_down = True
    logger.info("Shutting down bot...")
    
    try:
        # Закрытие соединения с базой данных
        await db.close()
        logger.info("✅ Соединение с базой данных закрыто")
        
        # Закрытие сессии бота
        await bot.session.close()
        logger.info("✅ Сессия бота закрыта")
        
        logger.info("✅ Бот успешно остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке: {e}")

def handle_signal(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}")
    asyncio.create_task(on_shutdown())

async def main():
    """Основная функция запуска бота"""
    try:
        # Регистрация обработчиков сигналов
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, handle_signal)
        
        # Set up startup and shutdown handlers
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Запуск бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        if not is_shutting_down:
            await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())