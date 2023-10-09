import os

root = os.getcwd()
 # 取得課程的模型路徑
model_path = os.path.join(root, "public", "static","attendance_records","abc","ccc","aaa")
if not os.path.exists(model_path):
    os.makedirs(model_path)