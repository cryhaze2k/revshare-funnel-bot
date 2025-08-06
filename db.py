# db.py
import sqlite3
from datetime import datetime

DB_NAME = 'bot_database.db'

def init_db():
    """Инициализирует базу данных и создает таблицы, если их нет."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей [cite: 513]
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                country TEXT,
                joined_at DATETIME,
                completed_steps INTEGER DEFAULT 0,
                ref_clicks INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Таблица партнерских ссылок [cite: 520]
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_links (
                country TEXT PRIMARY KEY,
                url TEXT NOT NULL
            )
        ''')
        
        # Добавляем начальные ссылки, если их нет [cite: 524]
        initial_links = [('CA', 'https://example.com/ca/ref123'), ('ES', 'https://example.com/es/ref456'), ('DEFAULT', 'https://example.com/default/ref789')]
        cursor.executemany("INSERT OR IGNORE INTO affiliate_links (country, url) VALUES (?, ?)", initial_links)
        
        conn.commit()

def add_or_update_user(user_id: int, username: str, country_code: str):
    """Добавляет нового пользователя или обновляет страну существующего."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, username, country, joined_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET country = excluded.country, is_active = TRUE",
            (user_id, username, country_code, datetime.now())
        )
        conn.commit()

def get_user_country(user_id: int) -> str | None:
    """Получает код страны пользователя."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT country FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_affiliate_link(country_code: str) -> str:
    """Получает партнерскую ссылку для страны."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM affiliate_links WHERE country = ?", (country_code,))
        result = cursor.fetchone()
        if result:
            return result[0]
        # Если для страны нет ссылки, возвращаем ссылку по умолчанию
        cursor.execute("SELECT url FROM affiliate_links WHERE country = 'DEFAULT'")
        return cursor.fetchone()[0]

def update_affiliate_link(country_code: str, new_url: str) -> bool:
    """Обновляет партнерскую ссылку. [cite: 488]"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Проверяем, существует ли такая страна в таблице
        cursor.execute("SELECT 1 FROM affiliate_links WHERE country = ?", (country_code,))
        if cursor.fetchone():
            cursor.execute("UPDATE affiliate_links SET url = ? WHERE country = ?", (new_url, country_code))
            conn.commit()
            return True
        return False

def log_final_click(user_id: int):
    """Логирует нажатие на финальную кнопку. [cite: 447]"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET ref_clicks = ref_clicks + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

def get_stats():
    """Собирает статистику для админа. [cite: 481]"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Общее количество пользователей
        cursor.execute("SELECT COUNT(user_id) FROM users WHERE is_active = TRUE")
        total_users = cursor.fetchone()[0]
        
        # Распределение по странам
        cursor.execute("SELECT country, COUNT(user_id) FROM users WHERE is_active = TRUE GROUP BY country")
        users_by_country = cursor.fetchall()
        
        # Общее количество кликов и по странам
        cursor.execute("SELECT u.country, SUM(u.ref_clicks) FROM users u JOIN affiliate_links al ON u.country = al.country WHERE u.ref_clicks > 0 GROUP BY u.country")
        clicks_by_country = cursor.fetchall()
        
        cursor.execute("SELECT SUM(ref_clicks) FROM users")
        total_clicks = cursor.fetchone()[0] or 0
        
        return {
            "total_users": total_users,
            "users_by_country": users_by_country,
            "clicks_by_country": clicks_by_country,
            "total_clicks": total_clicks
        }

def get_all_user_ids():
    """Возвращает ID всех активных пользователей для рассылки. [cite: 494]"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_active = TRUE")
        return [row[0] for row in cursor.fetchall()]

def set_user_inactive(user_id: int):
    """Деактивирует пользователя, который заблокировал бота."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = FALSE WHERE user_id = ?", (user_id,))
        conn.commit()