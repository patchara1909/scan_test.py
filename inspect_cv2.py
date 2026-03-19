import cv2, face_recognition
import numpy as np
from PIL import Image

# inspect with PIL
pil = Image.open('me.jpg')
print('PIL mode', pil.mode, 'format', pil.format, 'size', pil.size, 'info', pil.info)
img = cv2.imread('me.jpg')
print('cv2 load shape', img.shape, 'dtype', img.dtype)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
print('after convert', img.shape, 'dtype', img.dtype)
try:
    enc = face_recognition.face_encodings(img)
    print('encodings result', enc)
except Exception as e:
    import traceback
    print('error during encoding', e)
    traceback.print_exc()
