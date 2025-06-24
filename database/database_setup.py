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

conn.commit()
conn.close()
print("Database setup complete.")
