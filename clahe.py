import os

import cv2

from app.controllers.data_manager import load
from app.types import Status

path = '/Users/Yusaku.Eigen/Desktop/20250916_車室監視_道玄坂２車室_0915_0921/merged'
raw_dir = os.path.join(path, 'RAW')
infos, lots = load(path)

clahes = {
    '1x1': cv2.createCLAHE(clipLimit=4.0, tileGridSize=(1, 1)),
    '4x2': cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 2)),
    '8x4': cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 4))
}
ng_shadows = [info for info in infos if info.status == Status.NG_Shadow]

txts = []
for info in ng_shadows:
    img = cv2.imread(os.path.join(raw_dir, info.name() + '_raw.jpg'))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


    # --- 2. ROI領域を指定（x, y, w, h）---
    x, y, w, h = info.plate_xmin, info.plate_ymin, info.plate_width, info.plate_height
    roi = img[y:y+h, x:x+w].copy()

    output_dir = os.path.join('clahe_results', info.name())
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    txts.append(f'./test_sample_lpr 20250403050600551.bin mount_point/{info.name()} mount_point/{info.name()} {x} {y} {w} {h}')

    for name, clahe in clahes.items():
        # --- YUVに変換 ---
        yuv = cv2.cvtColor(roi, cv2.COLOR_RGB2YUV)
        y_channel, u_channel, v_channel = cv2.split(yuv)

        # --- CLAHE適用 ---
        y_eq = clahe.apply(y_channel)

        # --- 合成してRGBに戻す ---
        yuv_eq = cv2.merge((y_eq, u_channel, v_channel))
        roi_eq = cv2.cvtColor(yuv_eq, cv2.COLOR_YUV2RGB)

        # --- 元画像に反映 ---
        img_copy = img.copy()
        img_copy[y:y+h, x:x+w] = roi_eq

        # --- 保存 ---
        output_path = os.path.join(output_dir, f'{name}.jpg')
        cv2.imwrite(output_path, cv2.cvtColor(img_copy, cv2.COLOR_RGB2BGR))
        # print(f"Saved: {output_path}")


with open('clahe_results/lpr.sh', 'w') as f:
    f.write('#!/bin/bash\n\n')
    for line in txts:
        f.write(line + '\n')