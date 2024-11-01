
import os
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import psycopg
# Импорт функции обновления файлов

# Загрузка переменных окружения из .env
dotenv_path = Path('.') / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    raise FileNotFoundError(".env файл не найден. Создайте его в корневой директории проекта.")

class Config:
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN = os.getenv('BOT_TOKEN')

    # Настройки PostgreSQL
    POSTGRES_PASSWORD = os.getenv('DB_PASSWORD')

    # Настройки ChromaDB
    CHROMADB_PORT = int(os.getenv('CHROMADB_PORT', 8000))

    def __init__(self):
        self.start_postgres()
        self.start_chromadb()
        self.update_files()

    def start_postgres(self):
        print("Проверка статуса PostgreSQL...")
        if not self.is_service_running('postgresql'):
            print("PostgreSQL не запущен. Запуск сервиса PostgreSQL...")
            try:
                subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
                print("Сервис PostgreSQL запущен.")
                self.wait_for_postgres()
            except subprocess.CalledProcessError as e:
                print(f"Не удалось запустить PostgreSQL: {e}")
                raise
        else:
            print("PostgreSQL уже запущен.")
            self.wait_for_postgres()

    def start_chromadb(self):
        print("Проверка статуса ChromaDB...")
        if not self.is_service_running('chromadb'):
            print("ChromaDB не запущен. Запуск сервиса ChromaDB...")
            try:
                subprocess.run(['sudo', 'systemctl', 'start', 'chromadb'], check=True)
                print("Сервис ChromaDB запущен.")
                self.wait_for_chromadb()
            except subprocess.CalledProcessError as e:
                print(f"Не удалось запустить ChromaDB: {e}")
                raise
        else:
            print("ChromaDB уже запущен.")
            self.wait_for_chromadb()

    def is_service_running(self, service_name):
        try:
            result = subprocess.run(['systemctl', 'is-active', '--quiet', service_name])
            return result.returncode == 0
        except Exception as e:
            print(f"Ошибка при проверке статуса {service_name}: {e}")
            return False

    def wait_for_postgres(self, timeout=30):
        print("Ожидание готовности PostgreSQL...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                conn = psycopg.connect(
                    password=self.POSTGRES_PASSWORD,
                )
                conn.close()
                print("PostgreSQL готов к использованию.")
                return
            except psycopg.OperationalError:
                time.sleep(2)
        raise TimeoutError("PostgreSQL не готов в течение отведенного времени.")

    def wait_for_chromadb(self, timeout=30):
        print("Ожидание готовности ChromaDB...")
        import requests
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f'http://8000:{self.CHROMADB_PORT}/health')
                if response.status_code == 200:
                    print("ChromaDB готов к использованию.")
                    return
            except requests.ConnectionError:
                pass
            time.sleep(2)
        raise TimeoutError("ChromaDB не готов в течение отведенного времени.")

    def update_files(self):
        pass 

if __name__ == "__main__":
    try:
        config = Config()
    except Exception as e:
        print(f"Произошла ошибка при инициализации конфигурации: {e}")

