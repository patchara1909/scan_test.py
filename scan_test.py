import cv2
import face_recognition
from pyzbar.pyzbar import decode
import sqlite3
import re
import os
import sys
import numpy as np
from datetime import datetime, timedelta
import time

# ตรวจสอบเวอร์ชัน numpy เพื่อหลีกเลี่ยงปัญหา dlib/face_recognition
try:
    _np_major = int(np.__version__.split('.', 1)[0])
except Exception:
    _np_major = None

if _np_major is not None and _np_major >= 2:
    print(f"⚠️ Incompatible numpy version {_np_major} detected ({np.__version__}). face_recognition/dlib ต้องการ numpy 1.x.")
    print("   ให้รัน: pip install \"numpy<2\"\n")
    sys.exit(1)

# --- 1. ตั้งค่าพื้นฐาน ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'attendance.db')

# --- 2. ฟังก์ชันแก้ไขปัญหา "Unsupported image type" ---
def load_and_fix_image(path):
    """โหลดภาพด้วย OpenCV และบังคับแปลงเป็น 8-bit RGB มาตรฐาน"""
    try:
        # ใช้ OpenCV อ่านภาพ (รองรับไฟล์หลายแบบกว่า face_recognition โดยตรง)
        img = cv2.imread(path)
        if img is None:
            return None
        
        # บังคับแปลงเป็น 8-bit (กันพวกภาพ 16-bit หรือ CMYK)
        img = cv2.convertScaleAbs(img)
        
        # แปลงจาก BGR (OpenCV) เป็น RGB (face_recognition)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"⚠️ พยายามซ่อมแซมไฟล์ {os.path.basename(path)} แต่ไม่สำเร็จ: {e}")
        return None

# --- 3. โหลดข้อมูลใบหน้าจากฐานข้อมูล ---
known_face_encodings = []
known_face_names = []
known_face_ids = []

def save_attendance(student_id, name):
    """บันทึกการเช็คชื่อเข้าฐานข้อมูล"""
    try:
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (date, time, student_id, name, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (date_str, time_str, student_id, name, 'Success'))
        conn.commit()
        conn.close()
        
        print(f"💾 บันทึกสำเร็จ: {name} ({student_id}) เมื่อ {date_str} {time_str}")
        return True
    except Exception as e:
        print(f"❌ บันทึกไม่สำเร็จ: {e}")
        return False

def load_data():
    print(f"📂 กำลังตรวจสอบฐานข้อมูลที่: {DB_FILE}")
    if not os.path.exists(DB_FILE):
        print("❌ ไม่พบไฟล์ฐานข้อมูล attendance.db!")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, name FROM students")
        rows = cursor.fetchall()
        conn.close()

        for sid, sname in rows:
            # ตรวจสอบไฟล์ภาพ (ลองทั้ง .jpg และ .png)
            img_found = False
            for ext in ['.jpg', '.JPG', '.png']:
                img_path = os.path.join(BASE_DIR, f"{sid}{ext}")
                if os.path.exists(img_path):
                    img_found = True
                    break
            
            if img_found:
                # ใช้ฟังก์ชันซ่อมแซมภาพที่เราสร้างไว้
                image_rgb = load_and_fix_image(img_path)
                
                if image_rgb is not None:
                    encs = face_recognition.face_encodings(image_rgb)
                    if encs:
                        known_face_encodings.append(encs[0])
                        known_face_names.append(sname)
                        known_face_ids.append(str(sid))
                        print(f"✔️ โหลดสำเร็จ: {sname} ({sid})")
                    else:
                        print(f"⚠️ พบรูปภาพ {sid} แต่ AI ตรวจไม่พบใบหน้าในรูป")
                else:
                    print(f"❌ ไฟล์ภาพ {sid} มีปัญหาด้านรูปแบบข้อมูลสี")
            else:
                print(f"🔍 ไม่พบไฟล์ภาพสำหรับรหัส: {sid}")
        
        print(f"🚀 สรุป: โหลดข้อมูลนักศึกษาได้ทั้งหมด {len(known_face_names)} คน")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในระบบโหลดข้อมูล: {e}")

load_data()

# ตรวจสอบ: หากยังโหลดไม่ได้สักคน โปรแกรมจะหยุดเพื่อไม่ให้กล้องเปิดค้างเปล่าๆ
if len(known_face_ids) == 0:
    print("\n‼️ ระบบไม่สามารถรันได้เนื่องจากไม่มีข้อมูลใบหน้าที่พร้อมใช้งาน ‼️")
    print("คำแนะนำ: ลองใช้มือถือถ่ายรูปใบหน้าใหม่แล้วเซฟเป็น .jpg ลงในโฟลเดอร์นี้")
    sys.exit()

# --- 4. ระบบกล้องและการทำงาน ---
print("📸 กำลังเปิดกล้อง... (กด 'q' เพื่อออก)")
cap = cv2.VideoCapture(0)
state = 'QR'
expected_id, expected_name = None, None
face_scan_timeout = None
success_display_until = None
# สถานะสำหรับค้างกรอบหน้า 2 วินาที
displaying_match = False
match_start = 0
match_boxes = []

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        now = datetime.now()

        # ถ้าอยู่ในช่วงค้างกรอบ ให้ตรวจหน้าต่อเนื่องและอัพเดทพิกัดกรอบ
        if displaying_match:
            elapsed = time.time() - match_start
            
            # ตรวจหน้า update กรอบให้ตามหน้าใหม่
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locs = face_recognition.face_locations(rgb_small)
            expected_idx = known_face_ids.index(expected_id) if expected_id in known_face_ids else None
            match_boxes = []
            
            if face_locs:
                face_encs = face_recognition.face_encodings(rgb_small, face_locs)
                for (top, right, bottom, left), enc in zip(face_locs, face_encs):
                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2
                    if expected_idx is not None and True in face_recognition.compare_faces([known_face_encodings[expected_idx]], enc, tolerance=0.4):
                        box_color = (0, 255, 0)
                        label = "MATCH"
                    else:
                        box_color = (0, 0, 255)
                        label = "NOT MATCH"
                    match_boxes.append((left, top, right, bottom, box_color, label))
            
            # วาดกรอบที่อัพเดทแล้ว
            for (left, top, right, bottom, box_color, label) in match_boxes:
                cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

            if elapsed >= 2:
                # บันทึกสำเร็จหลังค้างครบ 2 วินาที
                save_attendance(expected_id, expected_name)
                success_display_until = now + timedelta(seconds=3)
                state = 'QR'
                displaying_match = False
                match_boxes = []
                print(f"✅ เช็คอินสำเร็จ: {expected_name}")
                cv2.waitKey(500)

        # แสดงผลเมื่อสำเร็จ
        if success_display_until and now < success_display_until:
            cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 15)
            cv2.putText(frame, f"WELCOME: {expected_name}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

        # โหมดสแกน QR
        elif state == 'QR':
            cv2.putText(frame, "STEP 1: SCAN QR CODE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            for obj in decode(frame):
                qr_data = obj.data.decode('utf-8').strip()
                clean_id = ''.join(re.findall(r"\d+", qr_data))
                
                if clean_id in known_face_ids:
                    idx = known_face_ids.index(clean_id)
                    expected_id, expected_name = clean_id, known_face_names[idx]
                    state, face_scan_timeout = 'FACE', now + timedelta(seconds=15)
                    print(f"📱 QR ผ่าน: กำลังรอสแกนหน้า {expected_name}")

        # โหมดสแกนใบหน้า
        elif state == 'FACE':
            remaining = int((face_scan_timeout - now).total_seconds())
            cv2.putText(frame, f"STEP 2: SCAN FACE ({remaining}s)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"TARGET: {expected_name}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

            if now > face_scan_timeout: state = 'QR'
            elif not displaying_match:  # เฉพาะเมื่อไม่ได้อยู่ในช่วงค้างกรอบ
                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                face_locs = face_recognition.face_locations(rgb_small)
                if face_locs:
                    face_encs = face_recognition.face_encodings(rgb_small, face_locs)

                    # วาดกรอบใบหน้าทุกใบ เพื่อให้เห็นว่าเรากำลังตรวจสอบรูปไหน
                    expected_idx = known_face_ids.index(expected_id) if expected_id in known_face_ids else None
                    match_found = False
                    current_boxes = []

                    for (top, right, bottom, left), enc in zip(face_locs, face_encs):
                        # ปรับกลับเป็นพิกัดของเฟรมจริง (เพราะเรา resize 0.5)
                        top *= 2
                        right *= 2
                        bottom *= 2
                        left *= 2

                        if expected_idx is not None and True in face_recognition.compare_faces([known_face_encodings[expected_idx]], enc, tolerance=0.4):
                            box_color = (0, 255, 0)
                            label = "MATCH"
                            match_found = True
                        else:
                            box_color = (0, 0, 255)
                            label = "NOT MATCH"

                        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
                        current_boxes.append((left, top, right, bottom, box_color, label))

                    if match_found and not displaying_match:
                        # เริ่มค้างกรอบ 2 วินาที
                        displaying_match = True
                        match_start = time.time()
                        match_boxes = current_boxes
        cv2.imshow('Attendance System', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 ออกจากโปรแกรมตามคำสั่ง (กด 'q')")
            break

except KeyboardInterrupt:
    print("\n🛑 ถูกยกเลิกโดยผู้ใช้ (KeyboardInterrupt)")

finally:
    if 'cap' in globals() and cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("📷 กล้องถูกปิดเรียบร้อยแล้ว")