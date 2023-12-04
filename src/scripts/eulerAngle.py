import cv2
import numpy as np
import dlib
import math
import os
root = os.getcwd()
detector = dlib.get_frontal_face_detector()
landmarks_dat_path = os.path.join(
    root, "src", "scripts", "shape_predictor_68_face_landmarks.dat")
predictor = dlib.shape_predictor(landmarks_dat_path)
POINTS_NUM_LANDMARK = 68

# 用dlib檢測關鍵點，回傳姿態估計需要的6個點坐標


def get_6_landmarks(img, size):
    # 因為使用的圖片是已經截下的人臉，所以邊框就用圖片的大小
    face_rectangle = dlib.rectangle(0, 0, size[1], size[0])
    # 取得人臉關鍵點
    landmarks = predictor(img, face_rectangle)
    # 如果沒有偵測到人臉關鍵點則回傳-1
    if landmarks.num_parts != POINTS_NUM_LANDMARK:
        return -1, None
    # 取得6個點坐標2D的影像關鍵點位置
    image_points = np.array([
        (landmarks.part(30).x, landmarks.part(30).y),     # 鼻尖 Nose tip: 31
        (landmarks.part(8).x, landmarks.part(8).y),       # 下巴 Chin: 9
        # 左眼左角 Left eye left corner: 37
        (landmarks.part(36).x, landmarks.part(36).y),
        # 右眼右角 Right eye right corner: 46
        (landmarks.part(45).x, landmarks.part(45).y),
        # 嘴巴左角 Left Mouth corner: 49
        (landmarks.part(48).x, landmarks.part(48).y),
        # 嘴巴右角 Right Mouth corner: 55
        (landmarks.part(54).x, landmarks.part(54).y)
    ], dtype="double")

    return 0, image_points

# 獲取旋轉向量和平移向量


def get_pose_estimation(img_size, image_points):
    # 3維模型的座標點 (使用一般的3D人臉模型的座標點)
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corne
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ])
    # 焦距[x,y]
    focal_length = img_size[1]
    # 取得中心點[x,y]
    center = (img_size[1]/2, img_size[0]/2)
    # 照像機參數 (Camera internals)
    '''
    f=焦距
    c=中心
    [fx, 0 , cx]
    [0 , fy, cy]
    [0 , 0 , 1 ]
    '''
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype="double"
    )
    # 扭曲係數
    dist_coeffs = np.zeros((4, 1))  # 假設沒有鏡頭的成像扭曲 (no lens distortion)

    # 使用OpenCV的solvePnP函數來計算人臉的旋轉與位移
    # (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix
    #                                                              , dist_coeffs, flags=cv2.CV_ITERATIVE)
    # 參數:
    #   model_points 3維模型的座標點
    #   image_points 2維圖像的座標點
    #   camera_matrix 照像機矩陣
    #   dist_coeffs 照像機扭曲係數
    #   flags: cv2.SOLVEPNP_ITERATIVE
    (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points,
                                                                  image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

    return success, rotation_vector, translation_vector, camera_matrix, dist_coeffs

# 從旋轉向量轉換為角度


def get_degree(rotation_vector):
    # calculate rotation angles
    theta = cv2.norm(rotation_vector, cv2.NORM_L2)

    # transformed to quaterniond
    w = math.cos(theta / 2)
    x = math.sin(theta / 2)*rotation_vector[0][0] / theta
    y = math.sin(theta / 2)*rotation_vector[1][0] / theta
    z = math.sin(theta / 2)*rotation_vector[2][0] / theta

    ysqr = y * y
    # pitch (x-axis rotation)
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + ysqr)
    pitch = math.atan2(t0, t1)

    # yaw (y-axis rotation)
    t2 = 2.0 * (w * y - z * x)
    if t2 > 1.0:
        t2 = 1.0
    if t2 < -1.0:
        t2 = -1.0
    yaw = math.asin(t2)

    # roll (z-axis rotation)
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (ysqr + z * z)
    roll = math.atan2(t3, t4)

    # 單位轉換:將弧度轉換為度
    Y = int((pitch/math.pi)*180)
    X = int((yaw/math.pi)*180)
    Z = int((roll/math.pi)*180)

    if Y > 0:
        Y = 180 - Y
    elif Y < 0:
        Y = -180 - Y

    return 0, Y, X, Z


# 接受已經裁切好的人臉圖片(圖片的長寬即為人臉的框架)
def get_euler_angle(im):
    size = im.shape
    if size[0] > 700:
        h = size[0] / 3
        w = size[1] / 3
        im = cv2.resize(im, (int(w), int(h)), interpolation=cv2.INTER_CUBIC)
        size = im.shape

    ret, image_points = get_6_landmarks(im, size)
    if ret != 0:
        print('get_6_landmarks failed')
        return {}

    ret, rotation_vector, translation_vector, camera_matrix, dist_coeffs = get_pose_estimation(
        size, image_points)
    if ret != True:
        print('get_pose_estimation failed')
        return {}

    ret, pitch, yaw, roll = get_degree(rotation_vector)

    # pitch 抬頭(+)/低頭(-)
    # yaw 右轉(+)/左轉(-)
    # roll 右傾(+)/左傾(-)

    return {"pitch": pitch, "yaw": yaw, "roll": roll}

# Testing...
# from PIL import Image
# import os
# root = os.getcwd()
# imgs = cv2.imread(os.path.join(root, "2.png"))
# print(get_euler_angle(imgs))
