import cv2
import os
from math import ceil
from retinaface import RetinaFace
from scipy.spatial.distance import euclidean
# 判斷圖片方向


def correct_direction(img):
    ''' 
    cv2的旋轉角度實際數字為0,1,2
    cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE
    作用於cv2.rotate(img,0)

    這裡我自己設定3為不轉向
    '''
    # RetinaFace偵測圖片是否出現人臉(沒有人的話會回傳tuple)
    detected_faces = RetinaFace.detect_faces(img)
    # 如果沒有人臉則回傳 -1
    if type(detected_faces) == tuple:
        return -1
    horizon_count = 0
    inverted_count = 0
    for face in detected_faces:
        # 取得右眼座標點[x,y]
        right_eye = detected_faces[face]["landmarks"]["right_eye"]
        # 取得左眼座標點[x,y]
        left_eye = detected_faces[face]["landmarks"]["left_eye"]
        # 計算如果左右眼的x靠得太近，代表拍攝方向是橫的
        if abs(left_eye[0] - right_eye[0]) < 0.5 * euclidean(left_eye, right_eye):
            # 紀錄判斷拍攝方向為橫的次數
            horizon_count += 1
        # 如果左右眼x的差過於小，代表拍攝方向為倒著的
        if left_eye[0] - right_eye[0] < -0.5 * euclidean(left_eye, right_eye):
            # 紀錄判斷拍攝方向為倒著的次數
            inverted_count += 1
    # 判斷的基準為總數的一半
    threshold = ceil(0.5*len(detected_faces))
    # 如果判斷拍攝方向為倒著的次數超過threshold，則回傳逆時針180度
    if inverted_count >= threshold:
        return 1
    # 如果兩數都小於threshold，則回傳0度
    elif inverted_count < threshold and horizon_count < threshold:
        return 3
    # 如果判斷拍攝方向為橫的次數超過一半，則逆時針旋轉90度
    if horizon_count >= threshold:
        img = cv2.rotate(img, 2)
    # 重置 inverted_count
    inverted_count = 0
    # 程式執行到這，代表原本有偵測到人，所以重新偵測旋轉後的圖片
    detected_faces = RetinaFace.detect_faces(img)
    # 如果沒有人臉則回傳逆時針270度
    if type(detected_faces) == tuple:
        return 0

    for face in detected_faces:
        # 取得右眼座標點[x,y]
        right_eye = detected_faces[face]["landmarks"]["right_eye"]
        # 取得左眼座標點[x,y]
        left_eye = detected_faces[face]["landmarks"]["left_eye"]
        # 如果左右眼x的差為負數，代表拍攝方向為倒著的
        if left_eye[0] - right_eye[0] < 0:
            # 紀錄判斷拍攝方向為倒著的次數
            inverted_count += 1
    # 判斷的基準為總數的一半
    threshold = ceil(0.5*len(detected_faces))
    # 如果判斷拍攝方向為倒著的次數超過threshold，則回傳逆時針270度
    if inverted_count >= threshold:
        return 0
    # 否則回傳逆時針90度
    return 2

# 回傳正確圖片並存下


def img_align(img_path):
    # 載入圖片
    img = cv2.imread(img_path)
    # 旋轉圖片並儲存
    direction = correct_direction(img)
    if direction == -1:
        direction = 3
    if not direction == 3:
        img = cv2.rotate(img, direction)
    # 存下正確方向的圖片
    cv2.imwrite(img_path, img)
    return img

# 回傳第一次偵測到人臉的照片idx


def frames_correct_direction(dir_path, frames):
    # 第一次出現偵測到人臉的照片idx
    idx = 0
    count = 1
    while idx < len(frames):
        # 讀取圖片的正確方向
        direction = correct_direction(cv2.imread(
            os.path.join(dir_path, frames[idx]["fileName"])))
        # 如果沒有偵測到任何人
        if direction == -1:
            idx += count
            count += 1
        else:
            print('frames[idx]["fileName"]', frames[idx]["fileName"])
            return idx
    return 0


# root = os.getcwd()
# path = os.path.join(root, "public", "static",
#                     "roll_call_original", "boom1.jpg")
# print("path", path)
# img = cv2.imread(path)
# dir = correct_direction(img)
# print(dir)
# cv2.imwrite(path, cv2.rotate(img, dir))
