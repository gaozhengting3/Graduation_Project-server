import os

import numpy as np
import cv2
import torch
from PIL import Image, ImageDraw, ImageFont

root = os.getcwd()
print(f"Root : {root}")

font_size = 30
weight_path = os.path.join(root, "yolov7", "weights", "yolov7.pt")
model = torch.hub.load("yolov7","custom",
weight_path, source="local",force_reload=True, trust_repo=True)

cap = cv2.VideoCapture(0)
while True:
    ret, img = cap.read()
    if ret:
        img = Image.fromarray(img).convert("RGB")
        results = model(img)
        df = results.pandas().xyxy[0]
        draw = ImageDraw.Draw(img)

    for idx in range(len(df)):
        conf, name = df.loc[idx]['confidence'], df.loc[idx]['name']
        if name == "person":
            xyxy = [ df.loc[idx]['xmin'], df.loc[idx]['ymin'], df.loc[idx]['xmax'], df.loc[idx]['ymax']]
            draw.rectangle(xyxy, outline=(255,0,0), width=5)
            draw.text((xyxy[0], xyxy[1] - font_size), f"{name}: {conf:.2f}", fill=(255,0,0))
        else:
            continue
    cv2.imshow("img", np.array(img))

    if cv2.waitKey(1) == ord('q'):
        break
