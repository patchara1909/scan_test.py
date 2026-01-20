import cv2
import face_recognition
import numpy as np
from pyzbar.pyzbar import decode
import os
import time
import csv
from datetime import datetime

# =================================================================
# ส่วนที่ 1: ตั้งค่าไฟล์บันทึกข้อมูล (Excel/CSV)
# =================================================================
log_file = "attendance.csv"
if not os.path.exists(log_file):
    with open(log_file, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Time', 'QR_Data', 'Name', 'Status'])

# =================================================================
# ส่วนที่ 2: โหลดข้อมูลใบหน้าต้นฉบับ
# =================================================================
print("กำลังโหลดข้อมูลใบหน้า... กรุณารอสักครู่")
image_path = "me.jpg" 

img_temp = cv2.imread(image_path)
your_image = cv2.cvtColor(img_temp, cv2.COLOR_BGR2RGB)
your_face_encoding = face_recognition.face_encodings(your_image)[0]
known_face_encodings = [your_face_encoding]
known_face_names = ["Miss Patcharaporn Khedkin"] # <-- แก้ชื่อของคุณตรงนี้

# =================================================================
# ส่วนที่ 3: เริ่มระบบกล้องและระบบจับเวลาถอยหลัง
# =================================================================
cap = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_SIMPLEX

current_step = 1 
student_data_from_qr = ""
is_recorded = False 
qr_scan_time = 0 # เก็บเวลาที่สแกน QR สำเร็จ
timeout_limit = 3 # ตั้งเวลาถอยหลัง (วินาที)

print("ระบบพร้อมใช้งาน! รอสแกน QR Code...")

while True:
    ret, frame = cap.read()
    if not ret: break

    status_bar_color = (0, 0, 0)
    instruction_text = ""

    # --- STEP 1: รอสแกน QR Code ---
    if current_step == 1:
        instruction_text = "STEP 1: Please Scan QR Code"
        status_bar_color = (0, 165, 255)
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            student_data_from_qr = obj.data.decode('utf-8')
            current_step = 2
            is_recorded = False
            qr_scan_time = time.time() # เริ่มนับเวลาทันทีที่สแกน QR ติด
            print(f"QR Scanned: {student_data_from_qr}")

        for obj in decoded_objects:
            pts = np.array([obj.polygon], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (255, 0, 0), 3)

    # --- STEP 2: สแกนใบหน้า (พร้อมระบบนับถอยหลัง 3 วิ) ---
    elif current_step == 2:
        # คำนวณเวลาที่ผ่านไป
        elapsed_time = time.time() - qr_scan_time
        remaining_time = max(0, timeout_limit - int(elapsed_time))
        
        instruction_text = f"STEP 2: Scan Face (Timeout in {remaining_time}s)"
        status_bar_color = (255, 0, 0)

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        
        # --- เงื่อนไขการ Reset ---
        # 1. ถ้าไม่เจอหน้าเลย และเวลาเกิน 3 วินาที
        if len(face_locations) == 0 and elapsed_time > timeout_limit:
            print("Timeout: No face detected. Resetting...")
            current_step = 1
            student_data_from_qr = ""
            continue

        # 2. ถ้าสแกนผ่านแล้ว (is_recorded) และเอาหน้าออกไปแล้ว
        if is_recorded and len(face_locations) == 0:
            current_step = 1
            student_data_from_qr = ""
            is_recorded = False
            continue

        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_loc in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"
            color = (0, 0, 255)

            if True in matches:
                name = known_face_names[0]
                color = (0, 255, 0)
                instruction_text = "ACCESS GRANTED: Recorded!"
                status_bar_color = (0, 255, 0)

                if not is_recorded:
                    now = datetime.now()
                    current_date = now.strftime("%Y-%m-%d")
                    current_time = now.strftime("%H:%M:%S")
                    
                    with open(log_file, mode='a', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        writer.writerow([current_date, current_time, student_data_from_qr, name, 'Success'])
                    
                    print(f"✔️ Recorded: {name}")
                    is_recorded = True 

            top, right, bottom, left = face_loc
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, bottom + 25), font, 0.8, color, 2)

    # --- แสดงผล GUI ---
    # แถบสถานะด้านบน
    cv2.rectangle(frame, (0, 0), (640, 50), status_bar_color, -1)
    cv2.putText(frame, instruction_text, (10, 35), font, 0.7, (255, 255, 255), 2)
    
    # ข้อมูล QR ที่กำลังรันอยู่ (โชว์ที่มุมซ้ายล่าง)
    if student_data_from_qr:
        cv2.putText(frame, f"ID: {student_data_from_qr}", (10, 450), font, 0.6, (255, 255, 0), 2)

    cv2.imshow('Smart Attendance System', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()