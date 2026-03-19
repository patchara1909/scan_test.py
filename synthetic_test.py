import numpy as np
import face_recognition
arr = np.zeros((100,100,3), dtype=np.uint8)
print('test array shape', arr.shape, arr.dtype, 'contiguous', arr.flags.c_contiguous)
try:
    print('encodings', face_recognition.face_encodings(arr))
except Exception as e:
    import traceback
    print('error', e)
    traceback.print_exc()

# try grayscale
arr2 = np.zeros((100,100), dtype=np.uint8)
print('grayscale shape', arr2.shape, arr2.dtype, 'contiguous', arr2.flags.c_contiguous)
try:
    print('encodings gray', face_recognition.face_encodings(arr2))
except Exception as e:
    import traceback
    print('gray error', e)
    traceback.print_exc()
