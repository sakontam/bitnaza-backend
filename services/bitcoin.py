import os
import sqlite3
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import requests
import time
from extensions import socketio
from dotenv import load_dotenv

# โหลดตัวแปรจาก .env
load_dotenv()

# สร้าง Blueprint สำหรับ Bitcoin
bitcoin_bp = Blueprint("bitcoin", __name__)

# กำหนด path ของ database แบบ absolute
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(THIS_DIR) 
DB_PATH = os.path.join(BASE_DIR, "bitnaza_data.db")

# ฟังก์ชันสำหรับกำหนด socketio
def set_socketio(sio):
    global socketio
    socketio = sio

# ฟังก์ชันดึงข้อมูลจาก Bitcoin API
def fetch_bitcoin_data():
    url = os.getenv("url")
    api_key = os.getenv("API_key")
    parameters = {
        "fsym": "BTC",
        "tsym": "THB",
        "limit": 1440,
        "aggregate": 1,
        "api_key": api_key,
    }
    try:
        response = requests.get(url, params=parameters)
        response.raise_for_status()
        data = response.json()
        if response.status_code == 200 and data["Response"] == "Success":
            return [
                {
                    "timestamp": datetime.fromtimestamp(item["time"]).strftime("%Y-%m-%d %H:%M:%S"),
                    "price": item["close"],
                    "high_24h": item["high"],
                    "low_24h": item["low"],
                    "volume_24h": item.get("volumeto", 0),
                    "market_cap": item.get("market_cap", 0),
                }
                for item in data["Data"]["Data"]
            ]
        else:
            print(f"Failed to fetch Bitcoin data: {data.get('Message', 'Unknown error')}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching Bitcoin data: {e}")
        return None

# ฟังก์ชันบันทึกข้อมูลลงในฐานข้อมูล SQLite
def save_to_database_and_emit_bitcoin(minute_data):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for entry in minute_data:
            cursor.execute(
                "SELECT COUNT(*) FROM bitcoin_prices WHERE timestamp = ?",
                (entry["timestamp"],),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO bitcoin_prices (timestamp, price, high_24h, low_24h, volume_24h, market_cap)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["timestamp"],
                        entry["price"],
                        entry["high_24h"],
                        entry["low_24h"],
                        entry["volume_24h"],
                        entry["market_cap"],
                    ),
                )
                socketio.emit(
                    "new_data",
                    {
                        "timestamp": entry["timestamp"],
                        "price": entry["price"],
                        "high_24h": entry["high_24h"],
                        "low_24h": entry["low_24h"],
                        "volume_24h": entry["volume_24h"],
                        "market_cap": entry["market_cap"],
                    },
                )
            else:
                print(f"Data with timestamp {entry['timestamp']} already exists.")
        conn.commit()
        print("Bitcoin data saved to database.")

# API ดึงข้อมูลจากฐานข้อมูล
@bitcoin_bp.route("/api/bitcoin", methods=["GET"])
def get_bitcoin_data():
    interval = request.args.get("interval", "15m")
    interval_mapping = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "12h": 720,
        "1d": 1440,
    }
    interval_minutes = interval_mapping.get(interval)
    if interval_minutes is None:
        return jsonify({"error": "Invalid interval"}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        query_prices = f"""
            SELECT timestamp, price
            FROM bitcoin_prices
            WHERE (strftime('%s', timestamp) / 60) % {interval_minutes} = 0
            ORDER BY timestamp ASC
        """
        cursor.execute(query_prices)
        rows = cursor.fetchall()

        query_high_low = """
            SELECT high_24h, low_24h, price
            FROM bitcoin_prices
            ORDER BY timestamp DESC
            LIMIT 1
        """
        cursor.execute(query_high_low)
        stats = cursor.fetchone()

        data = {
            "prices": [{"timestamp": row[0], "price": row[1]} for row in rows],
            "high_24h": stats[0] if stats else 0.0,
            "low_24h": stats[1] if stats else 0.0,
            "latest_price": stats[2] if stats else 0.0,
        }
    return jsonify(data)

# ฟังก์ชันดึงและบันทึกข้อมูลแบบเรียลไทม์
def fetch_bitcoin_real_time():
    while True:
        try:
            print("Starting Bitcoin data fetch cycle...")
            minute_data = fetch_bitcoin_data()
            if minute_data:
                save_to_database_and_emit_bitcoin(minute_data)
            print("Bitcoin data fetch cycle completed.")
        except Exception as e:
            print(f"Error during Bitcoin data fetch cycle: {e}")

        now = datetime.now()
        minutes_to_next_10 = 10 - (now.minute % 10)
        if minutes_to_next_10 == 0:
            minutes_to_next_10 = 10
        next_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_next_10)
        sleep_seconds = (next_time - now).total_seconds()
        if sleep_seconds < 0:
            sleep_seconds = 0
        time.sleep(sleep_seconds)
