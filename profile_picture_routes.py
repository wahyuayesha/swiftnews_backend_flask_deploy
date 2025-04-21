from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()
picture_bp = Blueprint('picture', __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

# koneksi database
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)

cursor = db.cursor()

# CREATE (POST) - Upload file foto profil
@picture_bp.route('/upload-profile-picture/<username>', methods=['POST'])
def upload_profile_picture(username):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    # update database
    cursor.execute("UPDATE users SET profile_picture = %s WHERE username = %s", (filename, username))
    db.commit()

    return jsonify({'message': 'Profile picture uploaded successfully'}), 200


# READ (GET) - ambil file foto profil dari folder uploads
@picture_bp.route('/uploads/<filename>')
def get_uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# READ (GET) - ambil foto profil sesuai username
@picture_bp.route('/get-user-profile-picture/<username>', methods=['GET'])
def get_profile(username):
    cursor.execute("SELECT username, profile_picture FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'username': user[0],
        'profile_picture_url': f"http://10.0.2.158:5000/uploads/{user[1]}"
    })

