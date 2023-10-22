import cv2
import numpy as np
from PIL import Image

print('load model..')
cap = cv2.VideoCapture(0)
print('load model done.')
while True:
    ret, img = cap.read()
    if ret:
        cv2.imshow("img", np.array(img))
    if cv2.waitKey(1) == ord('q'):
        break