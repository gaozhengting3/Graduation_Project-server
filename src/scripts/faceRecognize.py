import glob
import os
import uuid

import cv2
import dlib
import matplotlib.image as img
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from deepface import DeepFace
from IPython.display import display
from PIL import Image
from tqdm import tqdm

from mylib import prev_dir
''' 
resultObject = 
{
                "originImageSize":{ "width":0, "height":0},
                "peopleNumbers": 2,
                "recognizeResults": [
                    {
                    "id": "U0924014",
                    "facePosition": { "x": 0, "y": 0, "w": 0, "h": 0 },
                    "fileName": "123e4567-e89b-12d3-a456-426655440000.jpg"
                    },
                    ...,
                ]
}
'''
# 取得root的路徑 "C:\workspace\server"
root = os.getcwd()


def getRecognizeResult(img, detectedResults):
    # 建立將來要回傳的所有辨識結果
    recognizeResults = []

    for rectangle in detectedResults:

        result = {}
        y = rectangle.top()
        h = rectangle.height()
        x = rectangle.left()
        w = rectangle.width()

        facePosition = {"x": x, "y": y, "w": w, "h": h}
        # 紀錄facePosition至result
        result["facePosition"] = facePosition
        # 從圖片中截下人臉區域
        face = img[y:y+h, x:x+h]
        # 紀錄fileName至
        fileName = str(uuid.uuid1())
        result["fileName"] = fileName + ".jpg"
        # 取得record資料夾的路徑 C:\workspace\server\public\static\attendance_records
        records_path = os.path.join(
            root, "public", "static", "attendance_records")
        # 取得儲存record檔案(.jpg)的路徑
        file_path = os.path.join(records_path, fileName + '.jpg')
        plt.imsave(file_path, face)
        id = getIdentity(file_path)
        # 紀錄id至result
        result["id"] = id
        recognizeResults.append(result)
    return recognizeResults

# 取得單個人臉的辨識結果(id)


def getIdentity(img_path):
    # 取得人臉資料夾的路徑 "C:\workspace\server\private\users_face"
    faces_path = os.path.join(root, "private", "users_face")
    # 尋找相同人臉
    # ["VGG-Face", "Facenet", "OpenFace", "DeepFace", "DeepID", "ArcFace"]
    # 建立權重檔
    df = DeepFace.find(
        img_path=img_path,
        model_name='Facenet512',
        db_path=faces_path,
        detector_backend='mtcnn',
        enforce_detection=False)
    # 宣告紀錄id出現的次數的dictonary idFreq
    idFreq = {}
    # 定義權重為偵測到的人臉數
    # 排序越靠前的代表信任度越高，權重值由大到小遞減
    weight = len(df[0]["identity"])
    for identityPath in df[0]["identity"]:
        # ./images/detected_facec/U0924014/007.jpg
        # 取得id ( U0924014 )
        id = identityPath.split('/')[-2]
        # 是否為出現在字典內的id
        if id in idFreq:
            idFreq[id] += weight
        else:
            idFreq[id] = weight
        weight -= 1

    # 找出現頻率最高的人的id
    maxID = ""
    maxValue = -1
    for key, value in idFreq.items():
        if value > maxValue:
            maxID = key
            maxValue = value

    return maxID

# 主程式


def faceRecognize(file_name):
    global resultObject
    resultObject = {}
    # 取得record資料夾的路徑 C:\workspace\server\public\static\roll_call_original
    records_path = os.path.join(root, "public", "static", "roll_call_original")
    # 取得儲存 roll_call_original 檔案的路徑
    file_path = os.path.join(records_path, file_name)
    # 加载图像
    image = Image.open(file_path)
    image = image.convert('RGB')
    image = np.array(image)
    # 取得圖片大小
    height, width, _ = image.shape
    # 紀錄原始圖片的大小
    resultObject["originImageSize"] = {"width": width, "height": height}
    # 使用 dlib 偵測人脸
    detector = dlib.get_frontal_face_detector()
    # 取得人臉偵測結果(dlib.rectangle)每個人臉的方框
    detectedResults = detector(image, 0)
    # 紀錄偵測到的人臉數
    resultObject["poepleNumbers"] = len(detectedResults)
    # 取得人臉辨識結果
    recognizeResults = getRecognizeResult(image, detectedResults)
    # 紀錄人臉辨識結果
    resultObject["recognizeResults"] = recognizeResults

    return resultObject
