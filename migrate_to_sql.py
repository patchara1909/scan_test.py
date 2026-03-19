import sqlite3
import pandas as pd
import os

def migrate_data():
    # 1. ตั้งค่าชื่อไฟล์
    csv_file = 'students.csv'      # ไฟล์ต้นทาง (Excel/CSV)
    db_file = 'attendance.db'     # ไฟล์ปลายทาง (SQLite)

    # 2. ตรวจสอบว่ามีไฟล์ CSV ต้นทางไหม
    if not os.path.exists(csv_file):
        print(f"❌ ไม่พบไฟล์ {csv_file} กรุณาตรวจสอบชื่อไฟล์!")
        return

    print(f"🔄 กำลังอ่านข้อมูลจาก {csv_file}...")
    
    try:
        # 3. อ่านข้อมูลจาก CSV ด้วย Pandas
        df = pd.read_csv(csv_file)

        # 4. เชื่อมต่อกับ SQLite (ถ้ายังไม่มีไฟล์ .db ระบบจะสร้างให้เองอัตโนมัติ)
        conn = sqlite3.connect(db_file)
        
        # 5. โอนข้อมูลลงตาราง 'students'
        # index=False คือไม่เอาเลขแถวของ Excel ไปด้วย
        # if_exists='replace' คือถ้ามีข้อมูลเก่าอยู่แล้วให้เขียนทับ (เหมาะกับการล้างข้อมูลใหม่)
        df.to_sql('students', conn, if_exists='replace', index=False)
        
        # 6. สร้างตาราง 'attendance' รอไว้เลย (สำหรับเก็บประวัติเช็คชื่อ)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                student_id TEXT,
                name TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("-" * 30)
        print("✅ ย้ายข้อมูลสำเร็จ!")
        print(f"📂 ไฟล์ฐานข้อมูลที่ได้: {db_file}")
        print(f"📊 จำนวนนักเรียนที่นำเข้า: {len(df)} คน")
        print("-" * 30)

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == '__main__':
    migrate_data()