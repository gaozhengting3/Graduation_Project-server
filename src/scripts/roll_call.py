import glob
import os
import uuid
import cv2
from retinaface import RetinaFace
import numpy as np
import dlib
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Dense, Flatten, Activation, Input, \
    BatchNormalization, AveragePooling2D, Dropout
from keras.callbacks import ModelCheckpoint
from tensorflow.keras.utils import to_categorical
from keras_vggface.vggface import VGGFace
from keras import backend as K
from image_aligner import img_align
from mylib import prev_dir
from flask import abort
''' 
resultObject = 
{
    "originImageSize":{ "width":0, "height":0},
    "peopleNumbers": 2,
    "unknowns":[
                    {"facePosition": { "x": 0, "y": 0, "w": 0, "h": 0 },
                    "fileName": "123e4567-e89b-12d3-a456-426655440000.jpg"},...
                ]
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
# 載入dlib人臉偵測器
detector = dlib.get_frontal_face_detector()
# 模型可接受的圖片大小
IMG_WIDTH = 224
IMG_HEIGHT = 224
IMG_SIZE = (IMG_WIDTH, IMG_HEIGHT)
IMG_SHAPE = (IMG_WIDTH, IMG_HEIGHT, 3)

# 取得root的路徑 "C:\workspace\server"
root = os.getcwd()

# 建立訓練模型用的資料集


def make_dataset(dir_path, dir_names: list):
    # 如果沒有任何人則回傳400
    if len(dir_names) == 0:
        abort(400)
    X = []
    Y = []
    for index, dir_name in enumerate(dir_names):
        user_dir_path = os.path.join(dir_path, dir_name)
        # 避免檔案路徑不存在
        if not os.path.exists(user_dir_path):
            continue
        # 取得資料夾內的所有檔案路徑
        files_path = glob.glob(os.path.join(user_dir_path, "*"))
        # 將照片加入至X, 編號加入至Y
        for file_path in files_path:
            try:
                # 取得學生id
                img = cv2.resize(cv2.imread(file_path), IMG_SIZE)
                X.append(img)
                Y.append(index)
            except Exception as e:
                print(e)
                print("file_path", file_path)
    # 如果沒有任何人則回隨便符合格式的 np.array
    if X == [] or Y == []:
        return np.zeros(shape=(2, 224, 224, 3)), np.array([1, 0], [0, 1])
    X = np.array(X)
    Y = np.array(Y)
    Y = to_categorical(Y)
    return X, Y

# 建立模型


def build_model(model_path, id_list):
    # 使用者照片的資料夾路徑C:\workspace\server\private\users_face
    users_dir = os.path.join(root, "private", "users_face")
    # 如果沒有資料夾則創建一個
    if not os.path.exists(users_dir):
        os.makedirs(users_dir)
    # 建立模型訓練用的資料集
    X, Y = make_dataset(users_dir, id_list)
    # 取得輸出層的種類數量
    output_dim = len(id_list)

    input = Input(shape=IMG_SHAPE)
    # 載入VGGFace當作base_model
    base_model = VGGFace(model='resnet50', include_top=False)
    # 凍住base_model每層的權重
    for x in base_model.layers:
        x.trainable = False
    # 將(224,224,3)的張量當作輸入數據傳給 base_model
    # 得到 x 為 base_model 最後一層輸出的特徵
    func = K.function([base_model.get_layer(index=0).input],
                      base_model.get_layer(index=-2).output)
    x = func([input])
    x = AveragePooling2D((7, 7))(x)
    x = Dropout(0.5)(x)
    x = Flatten()(x)
    x = Dense(output_dim, name="Output_tensor")(x)
    x = Activation("softmax")(x)
    model = Model(inputs=input, outputs=x)

    model.compile(loss="categorical_crossentropy",
                  metrics=['accuracy'], optimizer='adam')
    try:
        # 設定 callback 來儲存最好的模型，訓練後會自動將模型存至 filepath
        checkpoint = ModelCheckpoint(
            filepath=model_path, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
        model.fit(X, Y, epochs=20, batch_size=16,
                  validation_split=0.1, callbacks=[checkpoint])
    except Exception as e:
        print(e)
        print("model_path", model_path)
# 重新訓練模型


def retrain(model_path, id_list):
    base_model = load_model(model_path)
    # 使用者照片的資料夾路徑C:\workspace\server\private\users_face
    users_dir = os.path.join(root, "private", "users_face")
    # 建立模型訓練用的資料集
    X, Y = make_dataset(users_dir, id_list)
    # 取得輸出層的種類數量
    output_dim = len(id_list)
    # 因為改變輸出的數量，所以不取輸出層的結果
    tensor = base_model.layers[-3].output
    # 改成理想的輸出層
    x = Dense(output_dim, name='Output_tensor')(tensor)
    x = Activation("softmax")(x)
    # 將數入層連接輸出層以建立出新的模型
    model = Model(inputs=base_model.input, outputs=x)
    model.compile(loss="categorical_crossentropy",
                  metrics=['accuracy'], optimizer='adam')
    # 設定 callback 來儲存最好的模型
    checkpoint = ModelCheckpoint(
        filepath=model_path, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
    # 訓練新的模型
    model.fit(X, Y, epochs=20, batch_size=16,
              validation_split=0.1, callbacks=[checkpoint])
    return

# 載入模型


def my_load_model(courseID, id_list, retrain_flag=False):
    model_path = os.path.join(
        root, "private", "courses", courseID, f"{courseID}.h5")
    # 如果模型不存在則訓練一個模型
    if not os.path.exists(model_path):
        build_model(model_path, id_list)
    # 如果課程的人員有變動則重新訓練模型
    if retrain_flag == True:
        retrain(model_path, id_list)
    model = load_model(model_path)
    return model

# 偵測人臉(mode 0 使用 dlib，1 使用 RetinaFace)


def my_detect_face(img, threshold=0.7, detect_mode='retina'):
    # 回傳bounding box的座標陣列
    x1_lsit, y1_lsit, x2_lsit, y2_lsit = [], [], [], []
    # RetinaFace偵測模式
    if detect_mode == "retina":
        '''
            使用 RetinaFace 偵測人脸取得座標點
            偵測成功則回傳dictionary
            {
                "face_1": {
                    "score": 0.9993440508842468,
                    "facial_area": [155, 81, 434, 443],
                    "landmarks": {
                        "right_eye": [257.82974, 209.64787],
                        "left_eye": [374.93427, 251.78687],
                        "nose": [303.4773, 299.91144],
                        "mouth_right": [228.37329, 338.73193],
                        "mouth_left": [320.21982, 374.58798]
                    }
                }
            }
            若是沒有偵測到任何人則會回傳tuple
        '''
        detected_faces = RetinaFace.detect_faces(img, threshold)
        # 沒有偵測到人的話回傳 False
        if type(detected_faces) == tuple:
            return False
        for info_key in detected_faces:
            # facial_area = [x1, y1, x2, y2]
            x1 = int(detected_faces[info_key]["facial_area"][0])
            y1 = int(detected_faces[info_key]["facial_area"][1])
            x2 = int(detected_faces[info_key]["facial_area"][2])
            y2 = int(detected_faces[info_key]["facial_area"][3])

            # 將座標點紀錄至list
            x1_lsit.append(x1)
            y1_lsit.append(y1)
            x2_lsit.append(x2)
            y2_lsit.append(y2)
    # Dlib偵測模式
    else:
        detected_faces = detector(img, 0)
        # 沒有偵測到任何人則回傳 False
        if len(detected_faces) == 0:
            return False
        for face in detected_faces:
            # 左上角的座標點
            y1 = face.top()      # Row的起點
            x1 = face.left()     # Column的起點
            h = face.height()   # 高
            w = face.width()    # 寬
            # 右下角的座標點
            x1 = max(0, x1)                             # 避免 x1 小於 0
            y1 = max(0, y1)                             # 避免 y1 小於 0
            x2 = min(img.shape[1], x1 + w)              # 避免 x2 超出邊界
            y2 = min(img.shape[0], y1 + h)              # 避免 y2 超出邊界

            # 將座標點紀錄至list
            x1_lsit.append(x1)
            y1_lsit.append(y1)
            x2_lsit.append(x2)
            y2_lsit.append(y2)

    return x1_lsit, y1_lsit, x2_lsit, y2_lsit

# 擴展人臉座標點至可以看見下巴和耳朵


def expand_xy(origin_xy, img_shape):
    x1_lsit, y1_lsit, x2_lsit, y2_lsit = origin_xy
    exp_x1, exp_y1, exp_x2, exp_y2 = [], [], [], []
    for i in range(len(x1_lsit)):
        w = x2_lsit[i]-x1_lsit[i]                   # 寬
        h = y2_lsit[i]-y1_lsit[i]                   # 高
        x1 = max(0, x1_lsit[i]-int(0.3*w))          # 避免 x1 小於 0
        y1 = y1_lsit[i]
        x2 = min(img_shape[1], x2_lsit[i] + int(0.3*w))     # 避免 x2 超出邊界
        y2 = min(img_shape[0], y2_lsit[i] + int(0.1*h))     # 避免 y2 超出邊界
        exp_x1.append(x1)
        exp_y1.append(y1)
        exp_x2.append(x2)
        exp_y2.append(y2)
    return exp_x1, exp_y1, exp_x2, exp_y2
# 辨識人臉


def predict(face_imgs, id_list, model):
    if len(face_imgs) != 0:
        func = K.function([model.get_layer(index=0).input],
                          model.get_layer("Output_tensor").output)
        face_imgs = np.array(face_imgs)
        # 如果照片中只有偵測到一個人臉，需要再增加一個維度使照片能放進模型
        if len(face_imgs.shape) == 3:
            # 增加一個維度使照片能放進模型
            face_imgs = np.expand_dims(face_imgs, axis=0)
        pred = model.predict(face_imgs)
        out_tensor = func([face_imgs])
        # 將One hot的Y轉成1維數字陣列，數字代表其id的index
        prediction = []
        # 紀錄已辨識出的人的idx及tensor
        # { id : [index, tensor] }
        prev_tensor = {}
        # 取得每個人的狀態
        for idx, single_pred in enumerate(pred):
            # 取得 id...
            # 取得最大的張量
            tensor = np.max(out_tensor[idx])
            # 取得預測出最高的信心度
            max_conf = np.max(single_pred)
            # 如果信心度低於閥值則視為Unknown
            if max_conf < 0.97:
                id = "unknown"
            else:
                id = id_list[np.argmax(single_pred)]
                # 如果已經辨識過的人出現
                if id in prev_tensor:
                    # 比較tensor的大小決定誰是正確的人
                    if tensor > prev_tensor[id][1]:
                        prediction[prev_tensor[id][0]] = "unknown"
                        prev_tensor[id][0] = idx
                        prev_tensor[id][1] = tensor
                    else:
                        id = "unknown"
                else:
                    prev_tensor[id] = [idx, tensor]
            prediction.append(id)

    return prediction


def getRecognizeResult(img, bb, courseID, id_list, retrain_flag):

    # 建立將來要回傳的所有辨識結果
    recognizeResults = []
    face_imgs = []
    file_paths = []
    for idx in range(len(bb[0])):
        result = {}
        # bb = [x1, y1, x2, y2]
        x1 = int(bb[0][idx])
        y1 = int(bb[1][idx])
        x2 = int(bb[2][idx])
        y2 = int(bb[3][idx])
        w = int(x2 - x1)
        h = int(y1 - y1)

        facePosition = {"x": x1, "y": y1, "w": w, "h": h}
        # 紀錄facePosition至result
        result["facePosition"] = facePosition

        # 紀錄 file_name 至 result
        file_name = str(uuid.uuid1())
        result["fileName"] = file_name + ".jpg"
        # 確認有attendance_records資料夾，若不存在則建立該資料夾
        # attendance_records_path = C:\workspace\server\public\static\attendance_records
        attendance_records_path = os.path.join(
            os.getcwd(), "public", "static", "attendance_records")
        if not os.path.exists(attendance_records_path):
            os.makedirs(attendance_records_path)
        # 取得儲存record檔案(.jpg)的路徑 C:\workspace\server\public\static\attendance_records\{file_name}.jpg
        file_path = os.path.join(
            root, "public", "static", "attendance_records", file_name + '.jpg')
        file_paths.append(file_path)
        # 儲存照片至 attendance_records
        face = cv2.resize(img[y1:y2, x1:x2], IMG_SIZE)
        cv2.imwrite(file_path, face)
        # 儲存照片至 face_imgs 等待模型預測
        face_imgs.append(face)
        # 儲存單個人臉的各項紀錄
        recognizeResults.append(result)
    # 載入模型
    model = my_load_model(courseID, id_list, retrain_flag)
    prediction = predict(face_imgs, id_list, model)
    # 紀錄每個 Unknown 的 index
    unknown_idx = []
    # 紀錄 Unknown 的資訊
    unknowns_info = []
    # 紀錄模型預測出的 id 至 result
    for idx, id in enumerate(prediction):
        if id == "unknown":
            unknown_idx.append(idx)
        recognizeResults[idx]["user"] = id
    # 將 recognizeResults 中 id 為 unknown 的結果轉移至unknowns_info(從後方往前去刪除，才不會導致out of index)
    for i in unknown_idx[::-1]:
        unknowns_info.append(recognizeResults[i])
        del recognizeResults[i]
    resultObject["unknowns"] = unknowns_info

    return recognizeResults

# 主程式


def roll_call(file_name, courseID, id_list, retrain_flag):
    global resultObject
    resultObject = {}
    # 設定課程的模型路徑
    # 取得record資料夾的路徑 "C:\workspace\server\\public\static\roll_call_original\{file_path}"
    file_path = os.path.join(root, "public", "static",
                             "roll_call_original", file_name)
    # 如果沒有資料夾則創建一個
    if not os.path.exists(prev_dir(file_path)):
        os.makedirs(prev_dir(file_path))
        # 回傳 500
        abort(500)
    # 載入圖片
    img = img_align(file_path)
    # 取得圖片大小
    height, width, _ = img.shape
    # 紀錄原始圖片的大小
    resultObject["originImageSize"] = {"width": width, "height": height}
    # 使用RetinaFace偵測人臉，回傳每個人臉的 bounding box
    bb = my_detect_face(img, detect_mode="retina")
    # 如果沒有偵測到任何人則終止並回傳
    if bb == False:
        resultObject["unknowns"] = []
        resultObject["recognizeResults"] = []
        resultObject["poepleNumbers"] = 0
        return resultObject
    # 延展原始圖片至耳朵、下巴，以利辨識人臉
    exp_xy = expand_xy(bb, img.shape)
    # 紀錄偵測到的人數(x1_list的長度)
    resultObject["poepleNumbers"] = len(bb[0])
    # 取得人臉辨識結果
    recognizeResults = getRecognizeResult(
        img, exp_xy, courseID, id_list, retrain_flag)
    # 紀錄人臉辨識結果
    resultObject["recognizeResults"] = recognizeResults

    return resultObject


# # 用來增加網路深度的block，輸入的張量與輸出相同
# def identity_block(input_tensor, filters):
#     filters1, filters2, filters3 = filters
#     # 先進行 1x1 卷積來達到升維或降維
#     x = Conv2D(filters1, kernel_size=(1, 1))(input_tensor)
#     x = BatchNormalization()(x)
#     x = Activation('relu')(x)
#     # 進行 3x3 卷積
#     x = Conv2D(filters2, kernel_size=(3, 3), padding='same')(x)
#     x = BatchNormalization()(x)
#     x = Activation('relu')(x)
#     # 再進行 1x1 卷積來達到升維或降維
#     x = Conv2D(filters3, kernel_size=(1, 1))(x)
#     x = BatchNormalization()(x)

#     x = layers.add([x, input_tensor])
#     x = Activation('relu')(x)
#     return x


# # 匹配輸入與輸出維度不同的 block
# def resnet_conv_block(input_tensor, filters):
#     filters1, filters2, filters3 = filters
#     # 先進行 1x1 卷積來達到升維或降維
#     x = Conv2D(filters1, kernel_size=(1, 1))(input_tensor)
#     x = BatchNormalization()(x)
#     x = Activation('relu')(x)
#     # 進行 3x3 卷積
#     x = Conv2D(filters2, kernel_size=(3,3), padding='same')(x)
#     x = BatchNormalization()(x)
#     x = Activation('relu')(x)
#     # 再進行 1x1 卷積來達到升維或降維
#     x = Conv2D(filters3, kernel_size=(1, 1))(x)
#     x = BatchNormalization()(x)
#     # 為了與x的張量匹配，input_tensor也進行 1x1 卷積來達到升維或降維
#     shortcut = Conv2D(filters3,kernel_size=(1, 1))(input_tensor)
#     shortcut = BatchNormalization()(shortcut)

#     x = layers.add([x, shortcut])
#     x = Activation('relu')(x)
#     return x

# Testing...
# id_list = ["hao", "lo", "ming", "ting", "xiang", "yan"]
# flag = False
# file_name = os.path.join(root, "public", "static",
#                          "roll_call_original", "034.jpg")
# courseID = "121IEA0052"
# # 設定課程的模型路徑
# model_path = os.path.join(root, "private", "courses",
#                           courseID, f"{courseID}.h5")
# # 若模型不存在則訓練一個模型
# if not os.path.exists(model_path):
#     build_model(model_path, id_list)
# # 載入人臉辨識模型
# model = load_model(model_path)
# print(roll_call(file_name, courseID, id_list, flag))
