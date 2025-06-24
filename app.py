from flask import Flask
from flask_cors import CORS
from extensions import socketio
import threading
from services.bitcoin import bitcoin_bp, fetch_bitcoin_real_time, set_socketio as set_bitcoin_socketio
from services.usd_to_thb import usd_to_thb_bp, fetch_usd_to_thb_real_time, set_socketio as set_usd_to_thb_socketio

app = Flask(__name__)
CORS(app)

# กำหนด `socketio` ให้ใช้งานกับ Flask app
socketio.init_app(app, cors_allowed_origins="*")

# ส่ง socketio ไปยังโมดูลต่าง ๆ
set_bitcoin_socketio(socketio)
set_usd_to_thb_socketio(socketio)

# ลงทะเบียน Blueprint
app.register_blueprint(bitcoin_bp)
app.register_blueprint(usd_to_thb_bp)

if __name__ == "__main__":
    # เริ่มต้น Thread สำหรับการดึงข้อมูล Bitcoin แบบเรียลไทม์
    bitcoin_thread = threading.Thread(target=fetch_bitcoin_real_time)
    bitcoin_thread.daemon = True
    bitcoin_thread.start()

    # เริ่มต้น Thread สำหรับการดึงข้อมูล USD/THB แบบเรียลไทม์
    usd_to_thb_thread = threading.Thread(target=fetch_usd_to_thb_real_time)
    usd_to_thb_thread.daemon = True
    usd_to_thb_thread.start()

    # รันแอป
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
