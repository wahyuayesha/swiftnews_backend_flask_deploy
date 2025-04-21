from flask import Blueprint, request, jsonify, session
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()
user_bp = Blueprint('user', __name__)


db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)

cursor = db.cursor(dictionary=True)

# -- ACCOUNT (USER) CRUD API

# CREATE (POST) - Registrasi User
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Validasi input
    if not username or not password or not email:
        return jsonify({'error': 'Missing required fields'}), 400

    # Cek apakah username atau email sudah ada
    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({'error': 'Username or email already exists'}), 400

    # Hash password sebelum disimpan ke database
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Simpan data registrasi ke database
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
    db.commit()

    user_id = cursor.lastrowid # Ambil ID user yang baru saja dibuat

    print("Success: User registered successfully")  # Tambahkan log
    return jsonify({'message': 'User registered successfully','id' : user_id}), 201


# CREATE (POST) - Login User
@user_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Ambil user dari database berdasarkan username
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    # Jika user tidak ditemukan
    if not user:
        return jsonify({'error': 'Username not found'}), 401

    # Ambil password hash dari database (string)
    hashed_password = user['password']  

    # Validasi password
    if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')): 
        return jsonify({'error': 'Invalid password'}), 401

    return jsonify({'message': 'Login successful', 'user': user}), 200


# READ (GET) - Ambil Data User
@user_bp.route("/get-user/<username>", methods=['GET'])
def get_users(username):
    cursor.execute("SELECT username, email FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user), 200


# UPDATE (PUT) - Update User
@user_bp.route("/update/<username>", methods=['PUT'])
def update_users(username):
    data = request.get_json()
    new_username = data.get('username')
    new_email = data.get('email')
    current_password = data.get('current_password')
    new_password = data.get('password')

    # Ambil data user yang akan diupdate
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verifikasi current password
    if not current_password or not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Current password is incorrect"}), 401

    # Jika username baru diberikan dan berbeda dari username lama
    if new_username and new_username != user['username']:
        cursor.execute("SELECT * FROM users WHERE username = %s", (new_username,))
        if cursor.fetchone():
            return jsonify({'error': 'New username already exists'}), 400

    # Hash password baru jika diberikan, jika tidak tetap pakai yang lama
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') if new_password else user['password']

    # Update data user
    cursor.execute(
        "UPDATE users SET username = %s, email = %s, password = %s WHERE username = %s",
        (new_username or user['username'], new_email or user['email'], hashed_password, username)
    )
    db.commit()

    return jsonify({'message': 'User updated successfully'}), 200


# DELETE (DELETE) - Hapus User
@user_bp.route("/delete/<username>", methods=['DELETE'])
def delete_user(username):
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'message': 'User deleted successfully'}), 200


# HTTP status code

# 200: OK 
# -> Permintaan berhasil diproses dan respons dikirim dengan data yang diminta.
# 201 : Created 
# -> Data baru berhasil dibuat di server.
# 400: Bad Request 
# -> Permintaan tidak valid.
# 401 : Unauthorized 
# -> Permintaan gagal karena user tidak memiliki izin (biasanya karena token/login salah).
# 403 : Forbidden 
# -> Server menolak permintaan meskipun user sudah login.
# 404: Not Found 
# -> Server tidak menemukan data yang diminta.
# 500: Internal Server Error 
# -> Server mengalami kesalahan internal. (seperti kesalahan database pada backend)

