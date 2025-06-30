import sqlite3
from flask import jsonify, request

class FavoriteService:
    def __init__(self, db_path="bitnaza_data.db"):
        self.db_path = db_path

    # ดึงรายการเหรียญที่ user กด fav
    def get_user_favorites(self, user_id):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT symbol FROM favorite WHERE user_id = ?", (user_id,))
            favorites = [row["symbol"] for row in cursor.fetchall()]
            return jsonify({"user_id": user_id, "favorites": favorites}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:
                conn.close()

    # เพิ่มเหรียญที่ fav
    def add_favorite(self, user_id):
        conn = None
        try:
            data = request.json
            symbol = data.get("symbol")

            if not symbol:
                return jsonify({"error": "Missing symbol"}), 400

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO favorite (user_id, symbol)
                VALUES (?, ?)
            """, (user_id, symbol))
            conn.commit()

            return jsonify({"message": f"{symbol} added to favorites"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:
                conn.close()

    # ลบเหรียญจาก fav
    def remove_favorite(self, user_id, symbol):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorite WHERE user_id = ? AND symbol = ?", (user_id, symbol))
            conn.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "Favorite not found"}), 404

            return jsonify({"message": f"{symbol} removed from favorites"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:
                conn.close()

    # เช็กว่าเหรียญนี้ถูก fav อยู่หรือเปล่า
    def is_favorited(self, user_id, symbol):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM favorite WHERE user_id = ? AND symbol = ?", (user_id, symbol))
            result = cursor.fetchone()
            return jsonify({"favorited": bool(result)}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:
                conn.close()
