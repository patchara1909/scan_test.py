import face_recognition
import numpy as np
from PIL import Image

path = 'me.jpg'
print('loading', path)
img = face_recognition.load_image_file(path)
print('shape dtype', img.shape, img.dtype)
print('min max', img.min(), img.max())
print('contiguous', img.flags['C_CONTIGUOUS'])
print('nbytes', img.nbytes)

try:
    enc = face_recognition.face_encodings(img)
    print('enc done', enc)
except Exception as e:
    import traceback; traceback.print_exc()
