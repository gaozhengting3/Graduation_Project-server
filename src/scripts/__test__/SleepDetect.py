import os

import cv2
import numpy as np
import torch
import dlib
from PIL import Image, ImageDraw, ImageFont
from tensorflow.keras.models import load_model
# 模型可接受的圖片大小
IMG_WIDTH = 224
IMG_HEIGHT = 224
IMG_SIZE = (IMG_WIDTH, IMG_HEIGHT)

root = os.getcwd()
print(f"Root : {root}")
########################刪除
course = "121IEA0052"
id_list = ["hao","lo","ming","ting","xiang","yan"]
########################刪除
font_size = 30
weight_path = os.path.join(root, "yolov7", "weights", "yolov7.pt")
yolo_model = torch.hub.load("yolov7","custom",
weight_path, source="local",force_reload=True, trust_repo=True)

# 取得課程的模型路徑
model_path = os.path.join(root, "private", "courses",course,f"{course}.h5")
# 載入人臉辨識模型
print('load model..')
model = load_model(model_path)
print('load model done.')

count = 0
FPS = 15
# 使用 dlib 偵測人脸
detector = dlib.get_frontal_face_detector()
cap = cv2.VideoCapture(0)
while True:
    latest_info = []
    latest_imgs = []
    ret, img = cap.read()
    if ret:
        img = Image.fromarray(img).convert("RGB")
        results = yolo_model(img)
        df = results.pandas().xyxy[0]
        draw = ImageDraw.Draw(img)
        print(len(df))
        for idx in range(len(df)):
            conf, name = df.loc[idx]['confidence'], df.loc[idx]['name']
            if name == "person":
                xyxy = [ df.loc[idx]['xmin'], df.loc[idx]['ymin'], df.loc[idx]['xmax'], df.loc[idx]['ymax'] ]
                draw.rectangle(xyxy, outline=(255,0,0), width=5)
                # 每5楨截一次圖
                # if count == 0:
                # 截下偵測到的人
                crop_img = np.array(img.crop(xyxy))
                # 取得人臉偵測結果(dlib.rectangle)每個人臉的方框
                detectedResults = detector(np.array(crop_img),1)
                if detectedResults == 0:
                    break
                x,y,w,h,max_area = 0,0,0,0,0
                # 取得最大的人臉
                for rectangle in detectedResults:
                    area = rectangle.height()*rectangle.width()
                    if area > max_area:
                        x = rectangle.left()
                        y = rectangle.top()
                        h = rectangle.height()
                        w = rectangle.width()
                        max_area = area
                if x<=0 or y<=0 or w<=0 or h<=0:
                    continue
                print(x,y,w,h)
                face = Image.fromarray(crop_img[y:y+h,x:x+w]).resize(IMG_SIZE)
                latest_imgs.append(np.array(face))
                # 儲存關於圖片的資訊
                latest_info.append( {"xyxy" : xyxy} )
            else:
                continue
    
        if count == 0:
            # 如果有偵測到一人以上(含)才繼續
            if len(latest_imgs)!=0:
                latest_imgs = np.array(latest_imgs)
                # 如果只有偵測到一個人，則增加一個維度使照片能放進模型
                if len(latest_imgs.shape) == 3:
                    latest_imgs = np.expand_dims(latest_imgs , axis=0)
                pred = model.predict(latest_imgs)
                for idx, single_pred in enumerate(pred):
                    confidence = np.max(single_pred)
                    if confidence>0.95:
                        id = id_list[np.argmax(single_pred)]
                    else:
                        id = "Unknown"
                    latest_info[idx]["Name"] = id
                    # 將辨識結果顯示在圖的左上方
                    draw.text((latest_info[idx]["xyxy"][0], latest_info[idx]["xyxy"][1] - font_size), f"{id}: {confidence:.2f}", fill=(255,0,0))
    cv2.imshow("img", np.array(img))
    # 每五楨辨識一次
    # count = (count + 1) % 4
    if cv2.waitKey(1000 // FPS) == ord('q'):
        break