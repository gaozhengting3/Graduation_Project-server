import glob
import os
import uuid

import dlib
import numpy as np
from PIL import Image

from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Dense, Conv2D, Flatten, Activation, Input, BatchNormalization
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

def make_dataset(dir_path, dir_names:list):
    X=[]
    Y=[]
    for index, dir_name in enumerate(dir_names):
        # 取得資料夾內的所有檔案路徑
        files_path = glob.glob(os.path.join(dir_path, dir_name,"*"))
        # 將照片加入至X, 編號加入至Y
        for file_path in files_path:
            # 取得學生id
            img = np.array(Image.open(file_path).resize(IMG_SIZE).convert("RGB"))
            X.append(img)
            Y.append(index)
    X = np.array(X)
    Y = np.array(Y)
    Y = to_categorical(Y)
    return X, Y

def make_model(model_path, X, Y, output_dim):

    input = Input(shape=IMG_SHAPE)
    # 載入VGGFace當作base_model
    base_model = VGGFace(model='resnet50', include_top=False)
    # 凍住base_model每層的權重
    for x in base_model.layers:
        x.trainable = False

    # 將(224,224,3)的張量當作輸入數據傳給 base_model
    # 得到 x 為 base_model 最後一層輸出的特徵
    x = base_model(input)
    x = Conv2D(filters=1024, kernel_size=(5,5), padding="same")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)
    x = Conv2D(filters=2048, kernel_size=(5,5), padding="same")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)
    x = Flatten()(x)
    x = Dense(128, activation="relu")(x)
    # 預設六個人
    output = Dense(output_dim, activation='softmax', name='final_predictions')(x)

    model = Model(inputs=input, outputs=output)

    model.compile(loss="categorical_crossentropy", metrics=['accuracy'], optimizer='adam')
    model.fit(X, Y, epochs=10, batch_size=64)
    model.save(model_path)

# 取得單個人臉的辨識結果(id)
def predict(face_imgs, id_list, model):
    face_imgs = np.array(face_imgs)
    # 如果照片中只有偵測到一個人臉，需要再增加一個維度使照片能放進模型
    if len(face_imgs.shape) == 3:
        # 增加一個維度使照片能放進模型
        face_imgs = np.expand_dims(face_imgs , axis=0)
    pred = model.predict(face_imgs)
    # 將One hot的Y轉成1維數字陣列，數字代表其id的index
    prediction = []
    for single_pred in pred:
        confidence = np.max(single_pred)
        if confidence>0.95:
            print(single_pred)
            id = id_list[np.argmax(single_pred)]
            print(id)
            prediction.append(id)
        else:
            prediction.append("不明")
            print(single_pred)
            print("不明")
    return prediction

def getRecognizeResult(img, detectedResults, id_list, model):
    # 建立將來要回傳的所有辨識結果
    recognizeResults = []
    face_imgs = []
    count = 0
    for rectangle in detectedResults:
        count += 1
        result = {}
        y = rectangle.top()
        h = rectangle.height()
        x = rectangle.left()
        w = rectangle.width()
        
        facePosition = { "x": x, "y": y, "w": w, "h": h }
        # 紀錄facePosition至result
        result["facePosition"]= facePosition
        # 從圖片中截下人臉區域
        # 將圖片縮放至模型可接受的大小(224,224)
        face = Image.fromarray(img[y:y+h,x:x+w]).resize(IMG_SIZE).convert("RGB")
        # 紀錄fileName至
        # fileName = str(uuid.uuid1())
        file_name = str(count)
        result["fileName"]= file_name + ".jpg"
        # 取得儲存record檔案(.jpg)的路徑 C:\workspace\server\public\static\attendance_records\{file_name}.jpg
        file_path = os.path.join(root, "public", "static", "attendance_records", file_name + '.jpg')
        # 儲存照片至attendance_records
        face.save(file_path)
        # 儲存照片至face_imgs等待模型預測
        face_imgs.append(np.array(face))
        # 儲存單個人臉的各項紀錄
        recognizeResults.append(result)
    prediction = predict(face_imgs, id_list, model)
    # 紀錄模型預測出的id至result
    for index, id in enumerate(prediction):
        recognizeResults[index]["_id"] = id
    return recognizeResults


# 主程式
def faceRecognize(file_name, course, id_list, flag):
    global resultObject
    resultObject = {}
    # 使用者照片的資料夾路徑C:\workspace\server\private\users_face
    users_dir = os.path.join(root,"private","users_face")
    # 建立模型訓練用的資料集
    X, Y = make_dataset(users_dir,id_list)
    # 取得輸出層的種類數量
    output_dim = len(id_list)
    # 取得record資料夾的路徑 "C:\workspace\server\\public\static\roll_call_original\{file_path}"
    file_path = os.path.join(root, "public", "static", "roll_call_original", file_name)
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
    detectedResults = detector(image,1)
    # 紀錄偵測到的人臉數
    resultObject["poepleNumbers"] = len(detectedResults)
    # 取得課程的模型路徑
    model_path = os.path.join(root, "private", "courses",course,f"{course}.h5")
    # 若模型不存在則訓練一個模型
    if not os.path.exists(model_path):
        make_model(model_path, X, Y, output_dim)
    # 如果課程的人員有變動
    if flag == True:
        retrain(model_path, X, Y, output_dim)
    # 載入模型
    model = load_model(model_path)
    # 取得人臉辨識結果
    recognizeResults = getRecognizeResult(image, detectedResults, id_list, model)
    # 紀錄人臉辨識結果
    resultObject["recognizeResults"] = recognizeResults

    return resultObject

def retrain(model_path, X, Y, out_dim):
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