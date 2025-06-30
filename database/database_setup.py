import sqlite3

# เชื่อมต่อไปยังฐานข้อมูล (หรือสร้างใหม่ถ้าไม่มี)
conn = sqlite3.connect('bitnaza_data.db')
cursor = conn.cursor()

# สร้างตารางสำหรับราคาของ Bitcoin ถ้ายังไม่มี
cursor.execute('''
CREATE TABLE IF NOT EXISTS bitcoin_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    price REAL,
    high_24h REAL,
    low_24h REAL,
    volume_24h REAL,
    market_cap REAL
)
''')

# สร้างตารางสำหรับอัตราแลกเปลี่ยน USD/THB ถ้ายังไม่มี
cursor.execute('''
CREATE TABLE IF NOT EXISTS usd_to_thb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    price REAL,
    high_24h REAL,
    low_24h REAL,
    volume_24h REAL,
    market_cap REAL
)
''')

# สร้างตาราง User ถ้ายังไม่มี
cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# สร้างตาราง Favorite ถ้ายังไม่มี (เพื่อให้ผู้ใช้กด Fav เหรียญที่สนใจ)
cursor.execute('''
CREATE TABLE IF NOT EXISTS favorite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL, -- เช่น BTC, ETH
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol),
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
)
''')

conn.commit()
conn.close()
print("Database setup complete.")
