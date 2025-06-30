import sqlite3
from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime


class UserService:
    def __init__(self, db_path="bitnaza_data.db"):
        self.db_path = db_path
        self.secret_key = "your-secret-key"

    def create_jwt(self, user_id):
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def decode_jwt(self, token):
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}

    def get_users(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, created_at FROM user")
            users = [dict(row) for row in cursor.fetchall()]
            return jsonify(users), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, created_at FROM user WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return jsonify(dict(row)), 200
            return jsonify({"message": "User not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    def add_user(self):
        conn = None  # ✅ ป้องกันปิด conn ก่อนมันถูก assign
        try:
            data = request.json
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            if not username or not email or not password:
                return jsonify({"error": "Missing required fields"}), 400

            hashed_password = generate_password_hash(password)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user (username, email, password)
                VALUES (?, ?, ?)
            """,
                (username, email, hashed_password),
            )
            conn.commit()
            return jsonify({"message": "User added successfully"}), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Username or email already exists"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:  # ✅ เพิ่มเช็คก่อนปิด
                conn.close()

    def edit_user(self, user_id):
        try:
            data = request.json
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if password:
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    """
                    UPDATE user SET username = ?, email = ?, password = ? WHERE id = ?
                """,
                    (username, email, hashed_password, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE user SET username = ?, email = ? WHERE id = ?
                """,
                    (username, email, user_id),
                )

            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            return jsonify({"message": "User updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    def delete_user(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            return jsonify({"message": "User deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    def login(self):
        try:
            data = request.json
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return jsonify({"error": "Missing username or password"}), 400

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, password FROM user WHERE username = ?",
                (username,),
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                token = self.create_jwt(user["id"])
                return (
                    jsonify(
                        {
                            "message": "Login successful",
                            "token": token,
                            "user": {
                                "id": user["id"],
                                "username": user["username"],
                                "email": user["email"],
                            },
                        }
                    ),
                    200,
                )
            return jsonify({"error": "Invalid credentials"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    # # login by google
    # def google_login(self):
    #     mysql_conn = None
    #     try:
    #         data = request.json
    #         access_token = data.get("access_token")

    #         if not access_token:
    #             return jsonify({"error": "Missing access_token"}), 400

    #         # ดึงข้อมูลผู้ใช้จาก Google API ด้วย access_token
    #         response = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}")
    #         if response.status_code != 200:
    #             return jsonify({"error": "Invalid Google access token"}), 400

    #         # ข้อมูลผู้ใช้ที่ได้รับจาก Google
    #         user_info = response.json()
    #         email = user_info.get("email")
    #         name = user_info.get("name")

    #         hashed_token = generate_password_hash(access_token)

    #         mysql_conn = self.mysql_pool.get_connection()
    #         cursor = mysql_conn.cursor(dictionary=True)

    #         # ตรวจสอบว่าผู้ใช้มีอยู่แล้วหรือไม่
    #         cursor.execute("SELECT id, provider FROM user WHERE email = %s", (email,))
    #         user = cursor.fetchone()

    #         if not user:
    #             # เพิ่มผู้ใช้ใหม่
    #             cursor.execute("""
    #                 INSERT INTO user (username, email, password, provider, disable, role)
    #                 VALUES (%s, %s, %s, 'google', 0, 'user')
    #             """, (name, email, hashed_token))
    #             mysql_conn.commit()

    #         elif user['provider'] != 'google':
    #             return jsonify({"error": "This email is already registered with another provider"}), 400

    #         else:
    #             # หากผู้ใช้มีอยู่แล้ว ให้ปรับปรุง access_token
    #             cursor.execute("""
    #                 UPDATE user
    #                 SET password = %s
    #                 WHERE email = %s AND provider = 'google'
    #             """, (hashed_token, email))
    #             mysql_conn.commit()

    #         return jsonify({
    #             "message": "Google Login successful",
    #         }), 200
    #     except requests.RequestException as e:
    #         return jsonify({"error": "Failed to connect to Google"}), 500
    #     except Error as e:
    #         print(f"MySQL Error: {e}")
    #         return jsonify({"error": "Database error"}), 500
    #     finally:
    #         # ตรวจสอบว่า mysql_conn ถูกสร้างขึ้นแล้วและยังคงเชื่อมต่อ
    #         if mysql_conn is not None and mysql_conn.is_connected():
    #             cursor.close()
    #             mysql_conn.close()

    # # login by facebook
    # def facebook_login(self):
    #     mysql_conn = None
    #     try:
    #         data = request.json
    #         access_token = data.get("access_token")

    #         if not access_token:
    #             return jsonify({"error": "Missing access_token"}), 400

    #         # ตรวจสอบ Access Token กับ Facebook API
    #         response = requests.get(
    #             f"https://graph.facebook.com/me?fields=name,email&access_token={access_token}"
    #         )

    #         if response.status_code != 200:
    #             return jsonify({"error": "Invalid Facebook access token"}), 400

    #         hashed_token = generate_password_hash(access_token)

    #         # ดึงข้อมูลผู้ใช้จาก Facebook
    #         user_info = response.json()
    #         email = user_info.get("email")
    #         name = user_info.get("name")

    #         if not email:
    #             return jsonify({"error": "Email is required from Facebook"}), 400

    #         mysql_conn = self.mysql_pool.get_connection()
    #         cursor = mysql_conn.cursor(dictionary=True)

    #         # ตรวจสอบว่าผู้ใช้มีอยู่แล้วหรือไม่
    #         cursor.execute("SELECT id, provider FROM user WHERE email = %s", (email,))
    #         user = cursor.fetchone()

    #         if not user:
    #             # เพิ่มผู้ใช้ใหม่
    #             cursor.execute("""
    #                 INSERT INTO user (username, email, password, provider, disable, role)
    #                 VALUES (%s, %s, %s, 'facebook', 0, 'user')
    #             """, (name, email, hashed_token))
    #             mysql_conn.commit()

    #         elif user['provider'] != 'facebook':
    #             return jsonify({"error": "This email is already registered with another provider"}), 400

    #         else:
    #             # หากผู้ใช้มีอยู่แล้ว ให้ปรับปรุง access_token
    #             cursor.execute("""
    #                 UPDATE user
    #                 SET password = %s
    #                 WHERE email = %s AND provider = 'facebook'
    #             """, (hashed_token, email))
    #             mysql_conn.commit()

    #         # ตอบกลับข้อมูลผู้ใช้
    #         return jsonify({
    #             "message": "Facebook Login successful",
    #         }), 200

    #     except requests.RequestException as e:
    #         print(f"Facebook API Error: {e}")
    #         return jsonify({"error": "Failed to connect to Facebook"}), 500
    #     except Error as e:
    #         print(f"MySQL Error: {e}")
    #         return jsonify({"error": "Database error"}), 500
    #     finally:
    #         # ปิดการเชื่อมต่อฐานข้อมูล
    #         if mysql_conn is not None and mysql_conn.is_connected():
    #             cursor.close()
    #             mysql_conn.close()
