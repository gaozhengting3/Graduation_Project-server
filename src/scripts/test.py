import os
from os import paths

root = os.getcwd()
 # 取得課程的模型路徑
model_path = os.path.join(root, "private", "courses","121IEA0052","121IEA0052.h5")
if os.path.exists(model_path):
    print("aaa")