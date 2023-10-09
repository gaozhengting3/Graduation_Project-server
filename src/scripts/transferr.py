import glob
import os
import uuid

import cv2
import dlib
import matplotlib.image as img
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from tqdm import tqdm

from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Dense, Dropout, Conv2D, Flatten, MaxPooling2D, Concatenate, Input, GlobalAveragePooling2D
from tensorflow.keras.utils import to_categorical
from keras_vggface.vggface import VGGFace

from mylib import prev_dir
''' 
resultObject = 
{
    "originImageSize":{ "width":0, "height":0},
    "peopleNumbers": 2,
    "recognizeResults": [
        {
        "_id": "mongoose.Types.ObjectId",
        "facePosition": { "x": 0, "y": 0, "w": 0, "h": 0 },
        "fileName": "123e4567-e89b-12d3-a456-426655440000.jpg"
        },
        ...,
    ]
}
'''
# 模型可接受的圖片大小
IMG_WIDTH = 224
IMG_HEIGHT = 224
IMG_SIZE = (IMG_WIDTH, IMG_HEIGHT)
IMG_SHAPE = (IMG_WIDTH, IMG_HEIGHT, 3)

# 取得root的路徑 "C:\workspace\server"
root = os.getcwd()

def make_model(model_path, id_list):
    #模型可以接受的X和結果Y
    X = []
    Y = []

    # 學生照片的資料夾路徑
    users_dir = []
    # 所有學生圖片的資料夾路徑 "C:\workspace\server\private\users_face\*"
    for user_id in id_list:
        users_dir.append((os.path.join(root,"private","users_face",user_id)))

    # 整理資料變成模型可以接受的X和Y
    for index, user_dir in enumerate(users_dir):
        # 取得當前學生的所有照片
        # "C:\workspace\server\private\users_face\U0924001\*"
        user_images_path = glob.glob(os.path.join(user_dir,"*"))
        # 將照片加入至X, 編號加入至Y
        for img_path in user_images_path:
            # 取得學生id
            img = np.array(Image.open(img_path).resize(IMG_SIZE).convert("RGB"))
            X.append(img)
            Y.append(index)
    X = np.array(X)
    Y = np.array(Y)
    Y = to_categorical(Y)

    input = Input(shape=IMG_SHAPE)
    # 載入VGGFace當作base_model
    base_model = VGGFace(model='resnet50', include_top=False)
    # 凍住base_model每層的權重
    for x in base_model.layers:
        x.trainable = False

    # 將(224,224,3)的張量當作輸入數據傳給 base_model
    # 得到 x 為 base_model 最後一層(AveragePooling2D)輸出的特徵
    x = base_model(input)
    x = Flatten()(x)
    x = Dense(2048, activation="relu")(x)
    x = Dense(1024, activation="relu")(x)
    x = Dense(512, activation="relu")(x)
    x = Dense(256, activation="relu")(x)
    x = Dense(128, activation="relu")(x)
    # 預設六個人
    output = Dense(len(id_list), activation='softmax', name='final_predictions')(x)

    model = Model(inputs=input, outputs=output)

    model.compile(loss="categorical_crossentropy", metrics=['accuracy'], optimizer='adam')
    model.fit(X, Y, epochs=10, batch_size=64)
    model.save(model_path)

# 取得單個人臉的辨識結果(id)
def getIdentity(face_img, id_list, model):
    # 增加一個維度使照片能放進模型
    face_img = np.expand_dims(face_img , axis=0)
    pred = model.predict(face_img)
    # 將One hot的Y轉成1維數字陣列，數字代表其id的index
    pred = np.argmax(pred, axis=1).astype(int)[0]
    id = id_list[pred]
    return id

def getRecognizeResult(img, detectedResults, id_list, model):
    # 建立將來要回傳的所有辨識結果
    recognizeResults = []

    for rectangle in detectedResults:

        result = {}
        y = rectangle.top()
        h = rectangle.height()
        x = rectangle.left()
        w = rectangle.width()
        
        facePosition = { "x": x, "y": y, "w": w, "h": h }
        # 紀錄facePosition至result
        result["facePosition"]= facePosition
        # 從圖片中截下人臉區域
        face = img[y:y+h,x:x+h]
        # 紀錄fileName至
        fileName = str(uuid.uuid1())
        result["fileName"]= fileName + ".jpg"
        # 取得record資料夾的路徑 C:\workspace\server\public\static\attendance_records
        records_path = os.path.join(root, "public", "static", "attendance_records")
        # 取得儲存record檔案(.jpg)的路徑
        file_path = os.path.join(records_path, fileName + '.jpg')
        plt.imsave(file_path, face)
        # 將圖片縮放至模型可接受的大小(224,224)
        face = np.array(Image.open(file_path).resize(IMG_SIZE).convert("RGB"))
        # reshape成模型可以輸入的X
        id = getIdentity(face, id_list, model)
        # 紀錄id至result
        result["_id"]= id
        recognizeResults.append(result)
    return recognizeResults


# 主程式
def faceRecognize(file_name, course, id_list, flag):
    global resultObject
    resultObject = {}
    # 取得record資料夾的路徑 "C:\workspace\server\\public\static\roll_call_original"
    records_path = os.path.join(root, "public", "static","roll_call_original")
    # 取得儲存 roll_call_original 檔案的路徑
    file_path = os.path.join(records_path, file_name)
    # 載入圖片
    image = Image.open(file_path)
    image = image.convert('RGB')
    image = np.array(image)
    # 取得圖片大小
    height, width, _ = image.shape
    # 紀錄原始圖片的大小
    resultObject["originImageSize"] = {"width" : width, "height" : height}
    # 使用 dlib 偵測人脸
    detector = dlib.get_frontal_face_detector()
    # 取得人臉偵測結果(dlib.rectangle)每個人臉的方框
    detectedResults = detector(image,0)
    # 紀錄偵測到的人臉數
    resultObject["poepleNumbers"] = len(detectedResults)

    # 取得課程的模型路徑
    model_path = os.path.join(root, "private", "courses",course,f"{course}.h5")
    # 若模型不存在則訓練一個模型
    if not os.path.exists(model_path):
        make_model(model_path, id_list)
    # 如果課程的人員有變動
    if flag == True:
        retrain(model_path, id_list)
    # 載入模型
    model = load_model(model_path)
    # 取得人臉辨識結果
    recognizeResults = getRecognizeResult(image, detectedResults, id_list, model)
    # 紀錄人臉辨識結果
    resultObject["recognizeResults"] = recognizeResults

    return resultObject

def retrain(model_path, id_list):
    # 學生照片的資料夾路徑
    users_dir = []
    # 所有學生圖片的資料夾路徑 "C:\workspace\server\private\users_face\*"
    for user_id in id_list:
        users_dir.append((os.path.join(root,"private","users_face",user_id)))
    
    #模型接受的X和結果Y
    X = []
    Y = []

    # 整理資料變成模型可以接受的X和Y
    for index, user_dir in enumerate(users_dir):
        # 取得當前學生的所有照片
        # "C:\workspace\server\private\users_face\U0924001\*"
        user_images_path = glob.glob(os.path.join(user_dir,"*"))
        # 將照片加入至X, 編號加入至Y
        for img_path in user_images_path:
            # 取得學生id
            img = np.array(Image.open(img_path).resize(IMG_SIZE).convert("RGB"))
            X.append(img)
            Y.append(index)
    X = np.array(X)
    Y = np.array(Y)
    print(Y.shape)
    print(Y)
    Y = to_categorical(Y)
    # 輸出層的結果數，也等於len(id_list)
    out_dim = Y.shape[1]
    # 載入原本的模型及權重
    base_model = load_model(model_path)
    
    # 凍住base_model倒數4層以前的權重
    for x in base_model.layers[0:-4]:
        x.trainable = False
    # 因為改變輸出的數量，所以不取輸出層的結果
    tensor = base_model.layers[-2].output
    # 改成理想的輸出層
    output = Dense(out_dim, activation='softmax',name='final_predictions')(tensor)
    # 將數入層連接輸出層以建立出新的模型
    model = Model(inputs=base_model.input, outputs=output)
    model.compile(loss="categorical_crossentropy", metrics=['accuracy'], optimizer='adam')
    # 訓練新的模型
    model.fit(X, Y, epochs=10, batch_size=64)
    # 儲存新的模型及權重檔
    model.save(model_path, overwrite = True)
    return