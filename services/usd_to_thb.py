import os
import sqlite3
import time
from dotenv import load_dotenv
from flask_socketio import emit
import requests
from flask import Blueprint, jsonify, request
from datetime import datetime
from extensions import socketio  # ใช้ socketio จาก extensions.py

usd_to_thb_bp = Blueprint("usd_to_thb", __name__)  # นิยาม Blueprint
load_dotenv()
# ฟังก์ชันสำหรับกำหนด socketio (หากต้องการเพิ่ม)
def set_socketio(sio):
    global socketio
    socketio = sio

def fetch_usd_to_thb_data():
    url = os.getenv("url")
    api_key = os.getenv("API_key")
    parameters = {
        "fsym": "USD",
        "tsym": "THB",
        "limit": 1440,
        "aggregate": 1,
        "api_key": api_key,
    }

    try:
        response = requests.get(url, params=parameters)
        response.raise_for_status()
        data = response.json()
        if data["Response"] == "Success":
            return [
                {
                    "timestamp": datetime.fromtimestamp(item["time"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "price": item["close"],
                    "high_24h": item["high"],
                    "low_24h": item["low"],
                    "volume_24h": item.get("volumeto", 0),
                    "market_cap": item.get("market_cap", 0),
                }
                for item in data["Data"]["Data"]
            ]
        return None
    except requests.RequestException as e:
        print(f"Error fetching USD/THB data: {e}")
        return None


def save_to_database_and_emit_usd_to_thb(data):
    with sqlite3.connect("bitnaza_data.db") as conn:
        cursor = conn.cursor()
        for entry in data:
            cursor.execute(
                "SELECT COUNT(*) FROM usd_to_thb WHERE timestamp = ?",
                (entry["timestamp"],),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO usd_to_thb (timestamp, price, high_24h, low_24h, volume_24h, market_cap)
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
                print(f"Inserted USD to THB data for {entry['timestamp']}")
                socketio.emit(
                    "new_usd_to_thb_data",
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
                print(f"USD/THB data for {entry['timestamp']} already exists.")
        conn.commit()
        print("USD To THB data saved to database.")

@usd_to_thb_bp.route("/api/usd-to-thb", methods=["GET"])
def get_usd_to_thb_data():
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

    with sqlite3.connect("bitnaza_data.db") as conn:
        cursor = conn.cursor()

        query_prices = f"""
            SELECT timestamp, price
            FROM usd_to_thb
            WHERE (strftime('%s', timestamp) / 60) % {interval_minutes} = 0
            ORDER BY timestamp ASC
        """
        cursor.execute(query_prices)
        rows = cursor.fetchall()

        query_high_low = """
            SELECT high_24h, low_24h, price
            FROM usd_to_thb
            ORDER BY timestamp DESC
            LIMIT 1
        """
        cursor.execute(query_high_low)
        stats = cursor.fetchone()

        data = {
            "prices": [{"timestamp": row[0], "price": row[1]} for row in rows],
            "high_24h": stats[0] if stats and stats[0] is not None else 0.0,
            "low_24h": stats[1] if stats and stats[1] is not None else 0.0,
            "latest_price": stats[2] if stats and stats[2] is not None else 0.0,
        }
    return jsonify(data)

def fetch_usd_to_thb_real_time():
    from datetime import datetime, timedelta
    while True:
        try:
            print("Starting USD/THB data fetch cycle...")
            usd_to_thb_data = fetch_usd_to_thb_data()
            if usd_to_thb_data:
                save_to_database_and_emit_usd_to_thb(usd_to_thb_data)
            print("USD/THB data fetch cycle completed.")
        except Exception as e:
            print(f"Error during USD/THB data fetch cycle: {e}")
        # คำนวณเวลาที่เหลือจนถึง 10 นาทีถัดไป (เช่น 23:10, 23:20, ...)
        now = datetime.now()
        minutes_to_next_10 = 10 - (now.minute % 10)
        if minutes_to_next_10 == 0:
            minutes_to_next_10 = 10
        next_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_next_10)
        sleep_seconds = (next_time - now).total_seconds()
        if sleep_seconds < 0:
            sleep_seconds = 0
        time.sleep(sleep_seconds)
