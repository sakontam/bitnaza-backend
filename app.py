import os
from flask import Flask, jsonify
from flask_cors import CORS
from auth import token_required
from extensions import socketio
import threading
from services.userService import UserService
from services.favoriteService import FavoriteService
from services.bitcoin import (
    bitcoin_bp,
    fetch_bitcoin_real_time,
    set_socketio as set_bitcoin_socketio,
)
from services.usd_to_thb import (
    usd_to_thb_bp,
    fetch_usd_to_thb_real_time,
    set_socketio as set_usd_to_thb_socketio,
)

app = Flask(__name__)
CORS(app)
userService = UserService(db_path="bitnaza_data.db")
favService = FavoriteService(db_path="bitnaza_data.db")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
# กำหนด `socketio` ให้ใช้งานกับ Flask app
socketio.init_app(app, cors_allowed_origins="*")

# ส่ง socketio ไปยังโมดูลต่าง ๆ
set_bitcoin_socketio(socketio)
set_usd_to_thb_socketio(socketio)

# ลงทะเบียน Blueprint
app.register_blueprint(bitcoin_bp)
app.register_blueprint(usd_to_thb_bp)


# API User
@app.route("/users", methods=["GET"])
@token_required
def get_users():
    return userService.get_users()


@app.route("/user/<int:user_id>", methods=["GET"])
@token_required
def get_user_by_id(user_id):
    return userService.get_user_by_id(user_id)


@app.route("/user", methods=["POST"])
def add_user():
    return userService.add_user()


@app.route("/user/<int:user_id>", methods=["PATCH"])
@token_required
def edit_user(user_id):
    return userService.edit_user(user_id)


@app.route("/user/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    return userService.delete_user(user_id)


@app.route("/login", methods=["POST"])
def login():
    return userService.login()


# ดึงรายการเหรียญที่ user กด Fav
@app.route("/user/<int:user_id>/favorites", methods=["GET"])
@token_required
def get_favorites(user_id):
    return favService.get_user_favorites(user_id)


# เพิ่มเหรียญที่ user กด Fav
@app.route("/user/<int:user_id>/favorites", methods=["POST"])
@token_required
def add_fav(user_id):
    return favService.add_favorite(user_id)


# ลบ Fav ออกจาก user
@app.route("/user/<int:user_id>/favorites/<symbol>", methods=["DELETE"])
@token_required
def remove_fav(user_id, symbol):
    return favService.remove_favorite(user_id, symbol)


# เช็กว่า Fav ไว้หรือยัง
@app.route("/user/<int:user_id>/favorites/<symbol>", methods=["GET"])
@token_required
def is_fav(user_id, symbol):
    return favService.is_favorited(user_id, symbol)


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
