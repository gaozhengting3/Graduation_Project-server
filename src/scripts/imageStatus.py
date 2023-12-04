import os
import cv2
import uuid
from eulerAngle import get_euler_angle
from eyeClosed import is_eye_closed
import roll_call
from image_aligner import correct_direction, frames_correct_direction
from roll_call import my_detect_face, expand_xy
from datetime import datetime
from tqdm import tqdm
# 模型可接受的圖片大小
IMG_WIDTH = 224
IMG_HEIGHT = 224
IMG_SIZE = (IMG_WIDTH, IMG_HEIGHT)
root = os.getcwd()
# 單位時間(圖片張數)
interval = 50
# 超過一段時間都有出現的話就算點名成功
rc_threshold = 30
# 取得每張圖片的人臉狀態


def get_status(dir_path, frames, start_time, courseID, id_list, detect_mode='dlib', late_seconds=15):
    # 宣告回傳結果用的 resultObject
    resultObject = {}
    # 紀錄 dir_path 至 resultObject["pathName"]
    resultObject["pathName"] = dir_path
    # 建立 resultObject["frames"] 儲存每張圖片的資訊
    resultObject["frames"] = []
    # 如果沒有任何frames則終止並回傳
    if len(frames) == 0:
        return resultObject
    # 載入模型
    model = roll_call.my_load_model(courseID, id_list)
    # 紀錄圖片是否滿足 interval 的計數器
    img_count = 0
    # 取得第一次偵測到人臉的照片idx
    first_face_idx = frames_correct_direction(dir_path, frames)
    # 讀取第一張有人的圖片的正確方向
    direction = correct_direction(cv2.imread(
        os.path.join(dir_path, frames[first_face_idx]["fileName"])))
    print("direction", direction)
    # 如果還是沒有偵測到人則不轉向
    if direction == -1:
        direction = 3
    # 統計狀態狀態時採取 Slide Window 方法，1代表偵測到狀態，0則否
    rc_window = {name: [] for name in id_list}
    # 統計的點名狀態roll_call_status(預設皆為 False)
    rc_status = {name: False for name in id_list}
    # 點名紀錄 roll_call_result
    rc_result = []
    # 取得上課開始時間
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    # 遍歷所有的圖片
    c = 0
    for frame in tqdm(frames):
        c += 1
        # 如果還未記錄至間隔數則圖片計數器加 1
        img_count += 1
        # 宣告人臉辨識用的圖片陣列
        to_pred_imgs = []
        # 宣告偵測狀態用的圖片陣列
        face_imgs = []
        # 宣告儲存圖片資訊的dictionary
        image_info = {}
        # 取得圖片時間
        date_time = frame["dateTime"]
        # 紀錄 date_time 至 image_info["dateTime"]
        image_info["dateTime"] = date_time
        # 取得圖片檔名
        file_name = frame["fileName"]
        # 紀錄 file_name 至 image_info["fileName"]
        image_info["fileName"] = file_name
        # 取得圖片檔案路徑
        image_path = os.path.join(dir_path, file_name)
        # 讀取圖片
        img = cv2.imread(image_path)
        # 如果有旋轉方向則旋轉圖片並儲存
        if not direction == 3:
            img = cv2.rotate(img, direction)
            cv2.imwrite(image_path, img)
        # 偵測人臉
        # 回傳[x1_lsit, y1_lsit, x2_lsit, y2_lsit]，沒有偵測到人則會回傳False
        faces_info = my_detect_face(img, detect_mode=detect_mode)
        # 如果沒有偵測到任何人臉則每個人全部紀錄 0
        if faces_info == False:
            # 宣告每位學生狀態結果的list
            image_info["results"] = []
            for id in id_list:
                # rool_call_window 增加 0
                rc_window[id].append(0)
                image_info["results"].append({"user": id, "result": None})
                if img_count >= interval:
                    rc_window[id].pop(0)
            resultObject["frames"].append(image_info)
            continue

        # 進行人臉辨識的圖片使用expand過的xy
        exp_xy = expand_xy(faces_info, img.shape)
        for idx in range(len(exp_xy[0])):
            x1 = exp_xy[0][idx]
            y1 = exp_xy[1][idx]
            x2 = exp_xy[2][idx]
            y2 = exp_xy[3][idx]
            # 將臉部圖像縮放至模型可接受大小
            face = cv2.resize(img[y1:y2, x1:x2], IMG_SIZE)
            to_pred_imgs.append(face)
        for idx in range(len(faces_info[0])):
            x1 = faces_info[0][idx]
            y1 = faces_info[1][idx]
            x2 = faces_info[2][idx]
            y2 = faces_info[3][idx]
            face = img[y1:y2, x1:x2]
            face_imgs.append(face)

        # 宣告每位學生狀態結果的list
        image_info["results"] = []
        # 進行人臉辨識
        recog_results = roll_call.predict(to_pred_imgs, id_list, model)
        # 紀錄出現過的id
        appeared_id = []
        for idx, id in enumerate(recog_results):
            result = {}
            # 判斷眼睛是否閉合
            eyes_closed = is_eye_closed(face_imgs[idx])
            # 取得面相角度
            euler_angle = get_euler_angle(face_imgs[idx])
            # 如果辨識結果為 Unknown 則換至下一張圖片
            if id == "unknown":
                continue
            else:
                # rool_call_window 增加 1
                rc_window[id].append(1)
                # 將學生狀態紀錄至 result{ eulerAngle: { pitch: 4, roll: -5, yaw: 22 }, eyesClosed: False}
                result["user"] = id
                result["result"] = {"eulerAngle": euler_angle,
                                    "eyesClosed": eyes_closed}
                # 紀錄出現的id
                appeared_id.append(id)
                image_info["results"].append(result)
        # 遍歷id_list來確認是否每個人都有辨識結果
        for id in id_list:
            # 如果在辨識結果中沒有被找到，則給予空 dictionary
            if id not in appeared_id:
                # rool_call_window 增加 0
                rc_window[id].append(0)
                image_info["results"].append({"user": id, "result": None})
        # 如果到達檢查的間格數則進行統計並記錄點名
        if img_count >= interval:
            for idx, id in enumerate(recog_results):
                # 如果是陌生人則跳過
                if id == "unknown":
                    continue
                result = {}
                # 如果出現次數超過閥值，則視為點名成立
                if sum(rc_window[id]) >= rc_threshold:
                    # 如果已經有點過名則跳過
                    if rc_status[id] == True:
                        continue
                    rc_status[id] = True
                    result["user"] = id
                    result["facePosition"] = {"x": faces_info[0][idx], "y": faces_info[1][idx],
                                              "w": faces_info[2][idx] - faces_info[0][idx], "h": faces_info[3][idx] - faces_info[1][idx]}
                    # 紀錄 file_name 至 result
                    face_file_name = str(uuid.uuid1()) + ".jpg"
                    result["fileName"] = face_file_name
                    face_file_path = os.path.join(
                        root, "public", "static", "attendance_records", face_file_name)
                    # 存下人臉以便顯示在介面上
                    cv2.imwrite(face_file_path, to_pred_imgs[idx])
                    # 紀錄點名時間 date_time
                    result["dateTime"] = date_time
                    # 取得時間差(秒)
                    diff_time = (datetime.strptime(
                        date_time, '%Y-%m-%dT%H:%M:%S.%fZ') - start_time).seconds
                    # 如果大於遲到時間就判定為遲到
                    if diff_time > late_seconds:
                        result["status"] = "遲到"
                        print("遲到 time:", diff_time)
                    else:
                        result["status"] = "準時"
                        print("準時 time:", diff_time)
                    rc_result.append(result)
            for id in id_list:
                rc_window[id].pop(0)
        resultObject["rollCallResults"] = rc_result
        resultObject["frames"].append(image_info)
    return resultObject


# Testing...
# dir_path = os.path.join(root, "public", "static",
#                         "roll_call_original")
# frames = [{"fileName": "040.jpg", "dateTime": "2023-11-11"},
#           {"fileName": "042.jpg", "dateTime": "2023-11-11"},
#           {"fileName": "043.jpg", "dateTime": "2023-11-11"}]
# courseID = "121IEA0052"
# id_list = ["hao", "lo", "ming", "ting", "xiang", "yan"]
# print(get_status(dir_path, frames, courseID,
#       id_list, detect_mode='dlib'))
