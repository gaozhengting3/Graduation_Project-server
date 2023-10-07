import os
from os import path
from PIL import Image

# 取得root的路徑 "C:\workspace\server"
root = os.getcwd()

fileName = '3f003a73-2618-4982-b505-f57fc7b67645-035.jpg'
# 取得record資料夾的路徑 "C:\workspace\server\private\roll_call_original"
records_path = os.path.join(root, "private", "roll_call_original")
# 取得儲存 roll_call_original 檔案的路徑
file_path = os.path.join(records_path, fileName)
# 加载图像
print("=============", file_path)
image = Image.open(file_path)

print(image)

print('Python script done.')
