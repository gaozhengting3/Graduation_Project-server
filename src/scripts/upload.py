import cv2
import os
import uuid
from image_aligner import correct_direction
from tqdm import tqdm
from roll_call import my_detect_face, expand_xy
# 決定要儲存的圖片數量
save_number = 120

root = os.getcwd()

# 影片轉成圖片


def vid2imgs(id, file_name):
    vid_path = os.path.join(
        root, "private", "users_face", id, file_name)
    imgs = []
    vc = cv2.VideoCapture(vid_path)
    while True:
        ret, vid_frame = vc.read()
        if ret:
            imgs.append(vid_frame)
        else:
            break
    vc.release()
    return imgs
# 將學生上傳的影片轉成圖片並儲存


def upload(id, file_name):
    vid_path = os.path.join(root, "private", "users_face", id, file_name)
    try:
        # 取得圖片
        imgs = vid2imgs(id, file_name)
        # 取得間隔數
        per_img = len(imgs) // save_number
        # 偵測第一張圖片的正確方向
        correct_dir = correct_direction(imgs[0])
        # 如果沒有偵測到人則旋轉180度
        if correct_dir == -1:
            correct_dir = 1
        for idx in tqdm(range(save_number)):
            img = imgs[idx * per_img]
            # 如果有旋轉方向則旋轉圖片
            if not correct_dir == 3:
                img = cv2.rotate(img, correct_dir)
            # 預設使用RetinaFace偵測人臉
            bb = my_detect_face(img, detect_mode="retina")
            # 如果沒有偵測到人臉則跳過
            if bb == False:
                continue
            # 擴展人臉座標點至可以看見下巴和耳朵
            exp_xy = expand_xy(bb, img.shape)
            # 如果有偵測到人臉
            if exp_xy != False:
                for idx in range(len(exp_xy[0])):
                    x1 = exp_xy[0][idx]
                    y1 = exp_xy[1][idx]
                    x2 = exp_xy[2][idx]
                    y2 = exp_xy[3][idx]
                    # 從圖片中截下人臉
                    img = img[y1:y2, x1:x2]
                    # 存下圖片
                    img_path = os.path.join(root, "private", "users_face",
                                            id, str(uuid.uuid1())+".jpg")
                    cv2.imwrite(img_path, img)
        # 移除影片檔
        if os.path.exists(vid_path):
            os.remove(vid_path)
    except Exception as e:
        print(e)
        print("vid_path", vid_path)

# Testing...
# upload("yan", "yan.mp4")
