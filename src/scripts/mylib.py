import os


def prev_dir(path, count=1):
    for i in range(0, count):
        path = os.path.dirname(path)  # 返回到上一層資料夾
    return path

# "C:\workspace\server\private\users_face\U0924001" 減去
# "C:\workspace\server\private\users_face\"
# id = user_path[len(prev_dir(user_path))+1:len(user_path)]
