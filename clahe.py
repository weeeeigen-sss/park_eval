import os
import sys

import cv2

from app.controllers.data_manager import load
from app.types import Status


clahes = {
    '1x1': cv2.createCLAHE(clipLimit=4.0, tileGridSize=(1, 1)),
    '4x2': cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 2)),
    '8x4': cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 4))
}


if len(sys.argv) == 2:
    txts = []

    for dir in os.listdir(sys.argv[1]):
        if dir.startswith('.'):
            continue
        if dir == 'clahe_results':
            continue

        if not os.path.isdir(os.path.join(sys.argv[1], dir)):
            continue

        print(dir)
        raw_dir = os.path.join(sys.argv[1], dir, 'RAW')
        infos, lots = load(os.path.join(sys.argv[1], dir))
        filter = [info for info in infos if info.status == Status.NG_Shadow]
        # filter = [info for info in infos if info.vehicle_status == 'Stop']

        print(len(infos), len(filter))


        # output_dir = os.path.join(sys.argv[1], dir, 'clahe_results')
        # if not os.path.exists(output_dir):
        #     os.makedirs(output_dir)

        for info in filter:
            img = cv2.imread(os.path.join(raw_dir, info.name() + '_raw.jpg'))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # --- 2. ROI領域を指定（x, y, w, h）---
            x, y, x1, y1 = info.plate_xmin, info.plate_ymin, info.plate_xmax, info.plate_ymax
            roi = img[y:y1, x:x1].copy()

            output_dir = os.path.join(sys.argv[1], 'clahe_results', dir, info.name())
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            cv2.imwrite(os.path.join(output_dir, 'original.bmp'), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

            txts.append(f'./test_sample_lpr 20250403050600551.bin mount_point/{dir}/{info.name()} mount_point/{dir}/{info.name()} {int(x * 640 / 2016)} {int(y * 480 / 1520)} {int(x1 * 640 / 2016)} {int(y1 * 480 / 1520)}')

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
                img_copy[y:y1, x:x1] = roi_eq

                # --- 保存 ---
                output_path = os.path.join(output_dir, f'{name}.bmp')
                cv2.imwrite(output_path, cv2.cvtColor(img_copy, cv2.COLOR_RGB2BGR))
                # print(f"Saved: {output_path}")

    with open(os.path.join(sys.argv[1], 'clahe_results', 'lpr.sh'), 'w') as f:
        f.write('#!/bin/bash\n\n')
        for line in txts:
            f.write(line + '\n')