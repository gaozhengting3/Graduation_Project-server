import os


def prev_dir(path, count=1):
    for i in range(0,count):
        path = os.path.dirname(path)  # 返回到上一層資料夾
    return path