from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()
DB_FILE = "website_database.db" # Отдельная база для сайта

# --- МОДЕЛИ ДАННЫХ (для получения данных с сайта) ---
class ServerCreate(BaseModel):
    name: str
    ip: str
    protocol: str
    api_url: str

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Таблица статистики (пока просто счетчики для сайта)
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, revenue INTEGER, subs INTEGER, users INTEGER)''')
    # Таблица серверов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ip TEXT,
            protocol TEXT,
            api_url TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    # Добавим нулевую статистику, если ее нет
    cursor.execute("SELECT COUNT(*) FROM stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (revenue, subs, users) VALUES (0, 0, 0)")
    conn.commit()
    conn.close()

init_db()

# --- ОТДАЕМ САЙТ ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- СТАТИСТИКА ---
@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT revenue, subs, users FROM stats LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return {"revenue": row[0], "active_subscriptions": row[1], "total_users": row[2], "traffic_tb": "0.0"}

# --- СЕРВЕРЫ: ПОЛУЧИТЬ ВСЕ ---
@app.get("/api/servers")
def get_servers():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, ip, protocol, api_url, is_active FROM servers")
    servers = [{"id": r[0], "name": r[1], "ip": r[2], "protocol": r[3], "api_url": r[4], "is_active": bool(r[5])} for r in cursor.fetchall()]
    conn.close()
    return servers

# --- СЕРВЕРЫ: ДОБАВИТЬ ---
@app.get("/api/servers") # Исправим, это GET, а нам нужен POST. Ниже правильный:
@app.post("/api/servers")
def add_server(server: ServerCreate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO servers (name, ip, protocol, api_url) VALUES (?, ?, ?, ?)", 
                   (server.name, server.ip, server.protocol, server.api_url))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# --- СЕРВЕРЫ: УДАЛИТЬ ---
@app.delete("/api/servers/{server_id}")
def delete_server(server_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

# --- СЕРВЕРЫ: ВКЛ/ВЫКЛ ---
@app.put("/api/servers/{server_id}/toggle")
def toggle_server(server_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE servers SET is_active = NOT is_active WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    return {"status": "toggled"}
