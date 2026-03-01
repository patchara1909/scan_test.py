import cv2
import face_recognition
import numpy as np
from pyzbar.pyzbar import decode
import time
import requests

IP = "192.168.1.129"
API_URL = f"http://{IP}:5000/verify_attendance"
MY_FACE = "me.jpg"

print("กำลังโหลดระบบ...")
my_img = face_recognition.load_image_file(MY_FACE)
my_encoding = face_recognition.face_encodings(my_img)[0]

cap = cv2.VideoCapture(0)
current_step = 1 # 1: QR, 2: Face
qr_data = ""
timer_start = 0

while True:
    ret, frame = cap.read()
    if not ret: break

    label = "STEP 1: SCAN QR CODE"
    color = (0, 140, 255)

    if current_step == 1:
        for obj in decode(frame):
            qr_data = obj.data.decode('utf-8')
            current_step = 2
            timer_start = time.time()
            print(f"QR Scanned: {qr_data}")

    elif current_step == 2:
        elapsed = time.time() - timer_start
        label = f"STEP 2: SCAN FACE ({int(5-elapsed)}s)"
        color = (255, 0, 0)
        
        if elapsed > 5: # หมดเวลาสแกนหน้า
            current_step = 1
            continue

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for enc in face_encodings:
            match = face_recognition.compare_faces([my_encoding], enc, tolerance=0.45)
            if True in match:
                payload = {"student_id": "6612247037", "student_name": "Miss Patcharaporn", "token": qr_data}
                try:
                    res = requests.post(API_URL, json=payload)
                    if res.status_code == 200:
                        label = "ATTENDANCE SUCCESS!"
                        color = (0, 255, 0)
                        cv2.rectangle(frame, (0,0), (640,50), color, -1)
                        cv2.putText(frame, label, (10,35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                        cv2.imshow('Scanner', frame)
                        cv2.waitKey(1500)
                        current_step = 1
                except: print("Server Error")

    cv2.rectangle(frame, (0,0), (640,50), color, -1)
    cv2.putText(frame, label, (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    cv2.imshow('Scanner', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()