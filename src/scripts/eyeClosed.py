import dlib
import os
from scipy.spatial import distance as dist

POINTS_NUM_LANDMARK = 68

root = os.getcwd()

landmarks_dat_path = os.path.join(
    root, "src", "scripts", "shape_predictor_68_face_landmarks.dat")
# 載入人臉關鍵點偵測器
predictor = dlib.shape_predictor(landmarks_dat_path)
# 計算人眼縱橫比
# 從眼睛最左邊的關鍵點順時針繞(例:右眼 36,37,38,39,40,41，左眼 42,43,44,45,46,47)
# eye = [(x,y),(x,y),...]


def get_ratio(eye):
    # 計算眼睛垂直方向上下關鍵點的距離
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    # 計算水平方向上的關鍵點的距離
    C = dist.euclidean(eye[0], eye[3])

    # 計算眼睛的縱橫比
    aspect_ratio = ((A + B) / 2) / C

    # 回傳眼睛的縱橫比
    return aspect_ratio


def is_eye_closed(img):
    size = img.shape
    # 因為使用的圖片是已經截下的人臉，所以邊框就用圖片的大小
    face_rectangle = dlib.rectangle(0, 0, size[1], size[0])
    # 取得人臉關鍵點
    landmarks = predictor(img, face_rectangle)
    # 如果沒有偵測到人臉關鍵點則回傳 False
    if landmarks.num_parts != POINTS_NUM_LANDMARK:
        return False

    # 取得左眼的關鍵點
    left_eye = []
    for i in range(36, 42):
        # 左眼的關鍵點 36,37,38,39,40,41
        left_eye.append((landmarks.part(i).x, landmarks.part(i).y))

    # 取得右眼的關鍵點
    right_eye = []
    for i in range(42, 48):
        # 右眼的關鍵點 42,43,44,45,46,47
        right_eye.append((landmarks.part(i).x, landmarks.part(i).y))
    # 取得左右眼的比率
    left_ratio = get_ratio(left_eye)
    right_ratio = get_ratio(right_eye)
    # 如果兩隻眼睛縱橫比小於0.2，視為眼睛閉上
    if left_ratio < 0.2 and right_ratio < 0.2:
        return True
    else:
        return False

# Testing...
# from PIL import Image
# import numpy as np
# import os
# root = os.getcwd()
# imgs = np.array(Image.open(os.path.join(root, "2.png")).convert('RGB'))
# print(is_eye_closed(imgs))
