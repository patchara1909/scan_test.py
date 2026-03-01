from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

STUDENT_DB = 'students.csv'
ATTENDANCE_DB = 'attendance.csv'
LAST_SCAN = {"student_id": "รอนักเรียนสแกน...", "student_name": "กำลังรอข้อมูล..."}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    sid = str(data.get('id'))
    birth = data.get('password') # วันเกิดจากช่องรหัสผ่าน
    
    if not os.path.exists(STUDENT_DB):
        return jsonify({"status": "error", "message": "ไม่พบฐานข้อมูลนักเรียน (students.csv)"})
    
    try:
        df = pd.read_csv(STUDENT_DB)
        # ตรวจสอบรหัสและวันเกิด (รูปแบบต้องตรงกับใน Excel เช่น 19/9/2547)
        user = df[(df['student_id'].astype(str) == sid) & (df['birth_date'] == birth)]
        
        if not user.empty:
            return jsonify({"status": "success", "name": user.iloc[0]['name']})
        else:
            return jsonify({"status": "error", "message": "รหัสนักศึกษาหรือวันเกิดไม่ถูกต้อง"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get_history', methods=['GET'])
def get_history():
    if not os.path.exists(ATTENDANCE_DB): return jsonify([])
    try:
        df = pd.read_csv(ATTENDANCE_DB)
        return jsonify(df.tail(20).to_dict(orient='records')[::-1])
    except: return jsonify([])

@app.route('/update_qr', methods=['POST'])
def update_qr():
    return jsonify({"status": "success"})

@app.route('/get_last_student', methods=['GET'])
def get_last_student():
    return jsonify(LAST_SCAN)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)