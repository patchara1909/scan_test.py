from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import socket
import os

app = Flask(__name__)
CORS(app)

DB_FILE = 'attendance.db'
# ตัวแปรเก็บสถานะการสแกนล่าสุดเพื่อส่งไปหน้าจอมือถือ
LAST_SCAN = {"student_id": "รอสแกน QR...", "student_name": "กำลังรอข้อมูลใบหน้า..."}

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # ช่วยให้เรียกข้อมูลด้วยชื่อคอลัมน์ได้
    return conn

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ระบบ Login เช็คชื่อจากตาราง students ใน SQLite
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    sid = str(data.get('id'))
    birth = data.get('password') 
    
    conn = get_db_connection()
    user = conn.execute('SELECT name FROM students WHERE student_id = ? AND birth_date = ?', 
                        (sid, birth)).fetchone()
    conn.close()

    if user:
        return jsonify({"status": "success", "name": user['name']})
    return jsonify({"status": "error", "message": "รหัสหรือวันเกิดไม่ถูกต้อง"})

# รับข้อมูลจากกล้อง (scan_test.py) มาอัปเดตหน้าจอ
@app.route('/update_attendance_status', methods=['POST'])
def update_status():
    global LAST_SCAN
    data = request.json
    LAST_SCAN = {
        "student_id": data.get("student_id"),
        "student_name": data.get("student_name")
    }
    return jsonify({"status": "success"})

@app.route('/get_last_student', methods=['GET'])
def get_last_student():
    return jsonify(LAST_SCAN)

# ดึงประวัติการเช็คชื่อ 10 รายการล่าสุด
@app.route('/get_history', methods=['GET'])
def get_history():
    try:
        conn = get_db_connection()
        records = conn.execute('SELECT date, time, name FROM attendance ORDER BY id DESC LIMIT 10').fetchall()
        conn.close()
        return jsonify([dict(row) for row in records])
    except:
        return jsonify([])

# แผนที่ QR token -> student_id
QR_TOKEN_MAP = {}

@app.route('/update_qr', methods=['POST'])
def update_qr():
    data = request.json or {}
    token = data.get('token')
    student_id = data.get('student_id')
    if token and student_id:
        QR_TOKEN_MAP[str(token)] = str(student_id)
    return jsonify({"status": "success"})

@app.route('/resolve_qr', methods=['GET'])
def resolve_qr():
    token = request.args.get('token')
    if not token:
        return jsonify({"status": "error", "message": "missing token"}), 400
    student_id = QR_TOKEN_MAP.get(str(token))
    if student_id:
        return jsonify({"status": "success", "student_id": student_id})
    return jsonify({"status": "error", "message": "not found"}), 404

if __name__ == '__main__':
    ip = get_ip_address()
    print("\n" + "="*50)
    print(f"🚀 SERVER RUNNING AT: http://{ip}:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)