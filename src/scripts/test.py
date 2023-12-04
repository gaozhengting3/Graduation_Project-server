import dlib
import cv2
import os
from retinaface import RetinaFace
import uuid
from scipy.spatial.distance import euclidean
# 回傳正確圖片並存下


def img_align(img_path):
    # 宣告人臉偵測器
    detector = dlib.get_frontal_face_detector()
    # 設定旋轉的角度[90, 180, 270]
    directions = [cv2.ROTATE_90_CLOCKWISE,
                  cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]
    # 載入圖片
    img = cv2.imread(img_path)
    # 宣告用來儲存最多偵測結果的圖片(預設為原圖)
    correct_img = img
    # 儲存偵測到的人臉數
    max_result = len(detector(img, 0))
    # 測試每個角度的圖片偵測結果
    for direction in directions:
        # 旋轉原圖片
        rotate_img = cv2.rotate(img, direction)
        # dlib偵測人臉並回傳偵測到的數量
        result = len(detector(rotate_img, 0))
        # RetinaFace偵測圖片是否出現人臉
        detected_faces = RetinaFace.detect_faces(img)
        # 沒有偵測到人的話跳過此圖片
        if type(detected_faces) == tuple:
            continue
        # 如果偵測出的人臉大於 max_result
        if result > max_result:
            # 更新最大偵測人臉數
            max_result = result
            # 更新正確的圖片
            correct_img = rotate_img
    # 存下正確方向的圖片
    cv2.imwrite(img_path, correct_img)
    return correct_img

# 判斷圖片方向


def correct_direction(img):
    # 宣告人臉偵測器
    detector = dlib.get_frontal_face_detector()
    # 設定旋轉的角度[90, 180, 270]
    directions = [cv2.ROTATE_90_CLOCKWISE,
                  cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]
    # 預設圖片正確的方向為 0
    # RetinaFace偵測圖片是否出現人臉(沒有人的話會回傳tuple)
    detected_faces = RetinaFace.detect_faces(img)
    right_eye = (detected_faces["face_1"]["landmarks"]["right_eye"]
                 [0], detected_faces["face_1"]["landmarks"]["right_eye"][1])
    # [x,y]
    left_eye = (detected_faces["face_1"]["landmarks"]["left_eye"]
                [0], detected_faces["face_1"]["landmarks"]["left_eye"][1])
    dis = dist.euclidean(right_eye, left_eye)
    # 如果臉是橫的，順時針旋轉90度
    if left_eye[0]-right_eye[0] < 0.5*dis:
        img = cv2.rotate(img, directions[0])

    detected_faces = RetinaFace.detect_faces(img)
    right_eye = (detected_faces["face_1"]["landmarks"]["right_eye"]
                 [0], detected_faces["face_1"]["landmarks"]["right_eye"][1])
    # [x,y]
    left_eye = (detected_faces["face_1"]["landmarks"]["left_eye"]
                [0], detected_faces["face_1"]["landmarks"]["left_eye"][1])
    # 如果左眼的x < 右眼的x，再旋轉180度
    if left_eye[0]-right_eye[0] < 0.5*dis:
        img = cv2.rotate(img, directions[1])
    # cosine = (斜邊**2 + 鄰邊**2 - 對邊**2) / (2 * 斜邊 * 鄰邊)
    cv2.imwrite(os.path.join(root, "private", "attendance-records", "121IEA0052",
                             "656b90a4e580688c11bbb529", f"{str(uuid.uuid1())}.jpg"), img)

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
            print("idx", idx)
            print('frames[idx]["fileName"]', frames[idx]["fileName"])
            return idx
    print("idx", 0)
    return 0


root = os.getcwd()
img = cv2.imread(os.path.join(root, "private", "attendance-records", "121IEA0052",
                 "656b90a4e580688c11bbb529", "1bc1a5ad-4874-449d-a7a8-d34046d58d31.jpg"))
correct_direction(img)
