import os
import csv
import json
from datetime import datetime, timezone, timedelta

from app.models.parking_info import ParkingInfo
from app.types import Status
from app.utlis import parse_timestamp, format_jst

def load(path: str):
    # Load metadata json
    meta_dir = os.path.join(path, 'META')
    if not os.path.exists(meta_dir):
        # For ebsim
        meta_dir = os.path.join(path, 't4meta')
        if not os.path.exists(meta_dir):
            return None, None
    
    threshold_jst = None
    param_json = os.path.join(path, 'param.json')
    if os.path.exists(param_json):
        with open(param_json, "r", encoding="utf-8") as f:
            params = json.load(f)
            if 'datetime' in params and 'format' in params:
                JST = timezone(timedelta(hours=9))
                threshold_jst = datetime.strptime(params['datetime'], params['format']).replace(tzinfo=JST)
                print('[param.json] Start timestamp:', format_jst(threshold_jst))

    
    json_files = [f for f in os.listdir(meta_dir) if f.endswith(".json")]
    json_files.sort()

    infos: list[ParkingInfo] = []
    lots = []

    # For ebsim, load ROI
    min_x = 0
    min_y = 0
    max_x = 0
    max_y = 0
    roi_path = os.path.join(path, 'roi.json')
    if os.path.exists(roi_path):
        with open(roi_path, "r", encoding="utf-8") as roi_f:
                roi_data = json.load(roi_f)
                min_x = roi_data.get("min_x", 0)
                min_y = roi_data.get("min_y", 0)
                max_x = roi_data.get("max_x", 0)
                max_y = roi_data.get("max_y", 0)
                print(f'ROI loaded: {min_x}, {min_y}, {max_x}, {max_y}')

    for json_file in json_files:
        info = ParkingInfo.create(os.path.join(meta_dir, json_file), min_x, min_y, max_x, max_y)
        if info is None:
            continue
        
        if threshold_jst:
            info_jst= parse_timestamp(info.timestamp)
            if info_jst < threshold_jst:
                continue
       
        infos.append(info)
        if not info.lot in lots:
            lots.append(info.lot)

    # Load label csv
    label_csv = os.path.join(path, 'label.csv')
    if os.path.exists(label_csv):
        with open(label_csv, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # header = next(reader)
            for row in reader:
                match = [info for info in infos if info.json_file == row['json']]
                if len(match) == 1:
                    if 'is_miss_in' in row:
                        match[0].is_miss_in = bool(int(row['is_miss_in']))

                    if 'is_miss_out' in row:
                        match[0].is_miss_out = bool(int(row['is_miss_out']))

                    if 'is_gt_unknown' in row:
                        match[0].is_gt_unknown = bool(int(row['is_gt_unknown']))

                    if 'is_first' in row:
                        match[0].is_first = bool(int(row['is_first']))

                    if 'status' in row:
                        match[0].status = Status(int(row['status']))
                else:
                    print(row['json'])

    return infos, lots

def save_label(path: str, infos: list[ParkingInfo]):
    path = os.path.join(path, 'label.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                'json',
                'Timestamp',
                'lot',
                'is_occupied',
                'is_uncertain',
                'vehicle_status',

                'vehicle_xmin', 'vehicle_ymin',
                'vehicle_xmax', 'vehicle_ymax',
                'vehicle_wdith', 'vehicle_height',
                'vehicle_score',

                'lpr_top', 'top_quality',
                'lpr_bottom', 'bottom_quality',

                'plate_xmin', 'plate_ymin',
                'plate_xmax', 'plate_ymax',
                'plate_width', 'plate_height',
                'plate_score',

                'plate_confidence',

                'plate_count',
                'vehicle_count',

                'is_miss_in',
                'is_miss_out',
                'is_gt_unknown',
                'is_first',
                'status',
                'status_label'
                ])
        for info in infos:
            writer.writerow(
                [
                    f'{info.json_file}',
                    f'{info.timestamp}',
                    f'{info.lot}', 
                    f'{int(info.is_occupied)}', 
                    f'{info.is_uncertain}',
                    f'{info.vehicle_status}',

                    f'{info.vehicle_xmin}', f'{info.vehicle_ymin}',
                    f'{info.vehicle_xmax}', f'{info.vehicle_ymax}',
                    f'{info.vehicle_wdith}', f'{info.vehicle_height}',
                    f'{info.vehicle_score}',

                    f'{info.lpr_top}', f'{info.top_quality}',
                    f'{info.lpr_bottom}', f'{info.bottom_quality}',

                    f'{info.plate_xmin}', f'{info.plate_ymin}',
                    f'{info.plate_xmax}', f'{info.plate_ymax}',
                    f'{info.plate_width}', f'{info.plate_height}',
                    f'{info.plate_score}',

                    f'{info.plate_confidence}',

                    f'{info.plate_count}',
                    f'{info.vehicle_count}',

                    f'{int(info.is_miss_in)}',
                    f'{int(info.is_miss_out)}',
                    f'{int(info.is_gt_unknown)}',
                    f'{int(info.is_first)}',
                    f'{info.status.value}',
                    f'{info.status}'
                    ])
    return path

def eval(lots, infos: list[ParkingInfo]):
    detect_all = []
    detect_ok = []

    ng_out = []
    ng_shadow = []
    ng_occlusion = []
    ng_fp = []
    ng_blur = []
    ng_overexposure = []
    ng_ai = []
    ng_others = []

    wrong_out = []

    is_miss_in = []
    is_miss_out = []
    is_gt_unknown = []

    resend = []
    is_occupied_last = False

    infos_wo_moving = [info for info in infos if info.vehicle_status != 'Moving']

    for lot in lots:
        for info in infos_wo_moving:
            if info.lot != lot:
                continue

            if info.status == Status.Wrong_Out:
                wrong_out.append(info)

            if info.is_miss_in:
                is_miss_in.append(info)
            if info.is_miss_out:
                is_miss_out.append(info)
            
            if info.is_occupied:
                detect_all.append(info)

                if is_occupied_last:
                    resend.append(info)

                if info.is_gt_unknown:
                    is_gt_unknown.append(info)

                if info.status == Status.OK:
                    detect_ok.append(info)
                elif info.status == Status.NG_Out:
                    ng_out.append(info)
                elif info.status == Status.NG_Shadow:
                    ng_shadow.append(info)
                elif info.status == Status.NG_Occlusion:
                    ng_occlusion.append(info)
                elif info.status == Status.NG_FP:
                    ng_fp.append(info)  
                elif info.status == Status.NG_Blur:
                    ng_blur.append(info)
                elif info.status == Status.NG_OverExposure:
                    ng_overexposure.append(info)
                elif info.status == Status.NG_AI:
                    ng_ai.append(info)
                elif info.status == Status.NG_Others:
                    ng_others.append(info)
                else:
                    print('Unknown status:', info.lot, info.timestamp)
            
            is_occupied_last = info.is_occupied

            # if info.status == Status.NoLabel:
            #     print('No label data exists.')

    detect_all_f = [info for info in detect_all if info.is_first == True]
    detect_ok_f = [info for info in detect_ok if info.is_first == True]
    wrong_out_f = [info for info in wrong_out if info.is_first == True]

    ng_out_f = [info for info in ng_out if info.is_first == True]
    ng_shadow_f = [info for info in ng_shadow if info.is_first == True]
    ng_occlusion_f = [info for info in ng_occlusion if info.is_first == True]
    ng_fp_f = [info for info in ng_fp if info.is_first == True]
    ng_blur_f = [info for info in ng_blur if info.is_first == True]
    ng_overexposure_f = [info for info in ng_overexposure if info.is_first == True]
    ng_ai_f = [info for info in ng_ai if info.is_first == True]
    ng_others_f = [info for info in ng_others if info.is_first == True]

    return {
        '検知総数': (
            len(detect_all),
            len(detect_all)
        ),
        '車両総数': (
            len(detect_all) - len(wrong_out) - len(ng_fp) - len(resend) + len(is_miss_out) + len(is_miss_in),
            len(detect_all) - len(wrong_out) - len(ng_fp) - len(resend) + len(is_miss_out) + len(is_miss_in),
        ),
        '入庫見逃し': (
            len(is_miss_in),
            len(is_miss_in),
        ),
        '出庫見逃し': (
            len(is_miss_out),
            len(is_miss_out),
        ),
        '誤出庫': (
            len(wrong_out),
            len(wrong_out_f),
        ),
        '全桁OK': (
            len(detect_ok),
            len(detect_ok_f),
        ),
        '全桁NG': (
            len(ng_out) + len(ng_shadow) + len(ng_occlusion) + len(ng_fp) + len(ng_blur) + len(ng_overexposure) + len(ng_ai) + len(ng_others),
            len(ng_out_f) + len(ng_shadow_f) + len(ng_occlusion_f) + len(ng_fp_f) + len(ng_blur_f) + len(ng_overexposure_f) + len(ng_ai_f) + len(ng_others_f),
        ),
        '全桁NG（見切れ）': (
            len(ng_out),
            len(ng_out_f),
        ),
        '全桁NG（影）': (
            len(ng_shadow),
            len(ng_shadow_f),
        ),
        '全桁NG（Occlusion）': (
            len(ng_occlusion),
            len(ng_occlusion_f),
        ),
        '全桁NG（FP）': (
            len(ng_fp),
            len(ng_fp_f),
        ),
        '全桁NG（Blur）': (
            len(ng_blur),
            len(ng_blur_f),
        ),
        '全桁NG（白飛び）': (
            len(ng_overexposure),
            len(ng_overexposure_f),
        ),
        '全桁NG（AIモデル）': (
            len(ng_ai),
            len(ng_ai_f),
        ),
        '全桁NG（その他）': (
            len(ng_others),
            len(ng_others_f),
        ),
        'GT不明': (
            len(is_gt_unknown),
            len(is_gt_unknown)
        ),
        '再送回数': (
            len(resend),
            len(resend)
        ),
        '全桁精度（メタごと）': (
            len(detect_ok) / len(detect_all),
            len(detect_ok_f) / len(detect_all_f) if len(detect_all_f) > 0 else 0
        ),
        '全桁精度（見切れ/FP抜き）': (
            len(detect_ok) / (len(detect_all) - len(ng_fp) - len(ng_out)),
            len(detect_ok_f) / (len(detect_all_f) - len(ng_fp_f) - len(ng_out_f)) if (len(detect_all_f) - len(ng_fp_f) - len(ng_out_f)) > 0 else 0
        )
}

def save_eval(path: str, lots, infos: list[ParkingInfo]):        
    eval_results = eval(lots, infos)

    path = os.path.join(path, 'eval.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['項目', 'meta', 'first'])
        for k,(all, first) in eval_results.items():
            writer.writerow([k, all, first])

    return path, eval_results