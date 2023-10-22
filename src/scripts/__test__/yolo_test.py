import os
import glob

root = os.getcwd()
train_path = "C:/workspace/server/yolov7/datasets/Person/images/train/*"
val_path = "C:/workspace/server/yolov7/datasets/Person/images/val/*"
train_txt = "C:\workspace\server\yolov7\datasets\Person/train_list.txt"
val_txt = "C:\workspace\server\yolov7\datasets\Person/val_list.txt"
with open(train_txt, 'w') as f:
    trains = glob.glob(train_path)
    for file in trains:
        f.write(file+'\n')

with open(val_txt, 'w') as f:
    vals = glob.glob(val_path)
    for file in vals:
        f.write(file+'\n')