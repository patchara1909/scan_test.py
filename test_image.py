import os
from PIL import Image
import numpy as np
import face_recognition

print("=" * 60)
print("🔍 ทดสอบการโหลดรูปภาพ me.jpg")
print("=" * 60)

image_path = "me.jpg"

# ตรวจสอบไฟล์
if not os.path.exists(image_path):
    print(f"❌ ไม่พบไฟล์: {image_path}")
    print(f"📁 ไฟล์ในโฟลเดอร์ปัจจุบัน:")
    for f in os.listdir('.'):
        print(f"   - {f}")
    exit()

print(f"✅ พบไฟล์: {image_path}")

try:
    # โหลดด้วย PIL
    print("\n1️⃣ โหลดด้วย PIL...")
    pil_image = Image.open(image_path)
    print(f"   - Format: {pil_image.format}")
    print(f"   - Size: {pil_image.size}")
    print(f"   - Mode: {pil_image.mode}")
    
    # แปลงเป็น RGB
    print("\n2️⃣ แปลงเป็น RGB...")
    pil_image = pil_image.convert('RGB')
    print(f"   - Mode หลังแปลง: {pil_image.mode}")
    
    # แปลงเป็น numpy array
    print("\n3️⃣ แปลงเป็น numpy array...")
    your_image = np.array(pil_image)
    print(f"   - Shape: {your_image.shape}")
    print(f"   - Dtype: {your_image.dtype}")
    print(f"   - Min/Max: {your_image.min()}/{your_image.max()}")
    
    # ตรวจสอบว่า uint8 หรือไม่
    if your_image.dtype != np.uint8:
        print(f"   ⚠️ Type ไม่ถูกต้อง! ต้องเป็น uint8 แต่ได้ {your_image.dtype}")
        your_image = your_image.astype(np.uint8)
        print(f"   ✅ แปลงเป็น uint8 แล้ว")
    
    # ค้นหาใบหน้า
    print("\n4️⃣ ค้นหาใบหน้า...")
    your_face_encodings = face_recognition.face_encodings(your_image)
    print(f"   - พบใบหน้า: {len(your_face_encodings)} อัน")
    
    if len(your_face_encodings) > 0:
        print("✅ สำเร็จ!")
    else:
        print("⚠️ ไม่พบใบหน้า ตรวจสอบรูปภาพ")
        
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}")
    print(f"   {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
