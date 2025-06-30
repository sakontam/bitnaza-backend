from functools import wraps
from dotenv import load_dotenv
from flask import request, jsonify
import jwt
import os

# โหลดค่า ENV
load_dotenv()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # ดึง token จาก Header
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Invalid or missing Authorization header"}), 401

        token = auth_header.split(" ")[1]

        try:
            # ดึง SECRET_KEY จาก ENV
            secret_key = os.getenv("SECRET_KEY")
            if not secret_key:
                raise ValueError("SECRET_KEY is not set in the environment")

            # Decode JWT
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # ส่งข้อมูลผู้ใช้ไปยังฟังก์ชันที่ถูกเรียก
        return f(*args, **kwargs)
    return decorated
