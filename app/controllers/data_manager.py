import os
import csv

from app.models.parking_info import ParkingInfo
from app.types import Status

def load(path: str):
    # Load metadata json
    meta_dir = os.path.join(path, 'META')
    if not os.path.exists(meta_dir):
        return None, None
    
    json_files = [f for f in os.listdir(meta_dir) if f.endswith(".json")]
    json_files.sort()

    infos: list[ParkingInfo] = []
    lots = []
    for json_file in json_files:
        info = ParkingInfo(os.path.join(meta_dir, json_file))
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
                'lot',
                'is_occupied',
                'is_uncertain',
                'vehicle_status',

                'vehicle_xmin',
                'vehicle_ymin',
                'vehicle_xmax',
                'vehicle_ymax',
                'vehicle_wdith',
                'vehicle_height',
                'vehicle_score',

                'lpr_top',
                'top_quality',
                'lpr_bottom',
                'bottom_quality',

                'plate_xmin',
                'plate_ymin',
                'plate_xmax',
                'plate_ymax',
                'plate_width',
                'plate_height',
                'plate_score',

                'plate_confidence',

                'is_miss_in',
                'is_miss_out',
                'is_gt_unknown',
                'status',
                'status_label'
                ])
        for info in infos:
            writer.writerow(
                [
                    f'{info.json_file}',
                    f'{info.lot}', 
                    f'{int(info.is_occupied)}', 
                    f'{info.is_uncertain}',
                    f'{info.vehicle_status}',

                    f'{info.vehicle_xmin}',
                    f'{info.vehicle_ymin}',
                    f'{info.vehicle_xmax}',
                    f'{info.vehicle_ymax}',
                    f'{info.vehicle_wdith}',
                    f'{info.vehicle_height}',
                    f'{info.vehicle_score}',

                    f'{info.lpr_top}',
                    f'{info.top_quality}',
                    f'{info.lpr_bottom}',
                    f'{info.bottom_quality}',

                    f'{info.plate_xmin}',
                    f'{info.plate_ymin}',
                    f'{info.plate_xmax}',
                    f'{info.plate_ymax}',
                    f'{info.plate_width}',
                    f'{info.plate_height}',
                    f'{info.plate_score}',

                    f'{info.plate_confidence}',

                    f'{int(info.is_miss_in)}',
                    f'{int(info.is_miss_out)}',
                    f'{int(info.is_gt_unknown)}',
                    f'{info.status.value}',
                    f'{info.status}'
                    ])
    return path

def save_eval(path: str, lots, infos: list[ParkingInfo]):        
    detect_all = detect_ok = 0
    ng_out = ng_shadow = ng_occlusion = ng_fp = ng_blur = ng_others = 0
    wrong_out = 0
    is_miss_in = is_miss_out = is_gt_unknown = 0

    resend = 0
    is_occupied_last = False

    for lot in lots:
        for info in infos:
            if info.lot != lot:
                continue

            if info.status == Status.Wrong_Out:
                wrong_out += 1

            if info.is_miss_in:
                is_miss_in += 1
            if info.is_miss_out:
                is_miss_out += 1
            
            if info.is_occupied:
                detect_all += 1

                if is_occupied_last:
                    resend += 1

                if info.is_gt_unknown:
                    is_gt_unknown += 1

                if info.status == Status.OK:
                    detect_ok += 1
                elif info.status == Status.NG_Out:
                    ng_out += 1
                elif info.status == Status.NG_Shadow:
                    ng_shadow += 1
                elif info.status == Status.NG_Occlusion:
                    ng_occlusion += 1
                elif info.status == Status.NG_FP:
                    ng_fp += 1  
                elif info.status == Status.NG_Blur:
                    ng_blur += 1
                elif info.status == Status.NG_Others:
                    ng_others += 1
            
            is_occupied_last = info.is_occupied

            if info.status == Status.NoLabel:
                print('No label data exists.')


    path = os.path.join(path, 'eval.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows([
                ['検知総数', detect_all],
                ['車両総数', detect_all - wrong_out - ng_fp - resend + is_miss_out],
                ['入庫見逃し', is_miss_in],
                ['出庫見逃し', is_miss_out],
                ['誤出庫', wrong_out],
                ['全桁OK', detect_ok],
                ['全桁NG', ng_out + ng_shadow + ng_occlusion + ng_fp + ng_blur + ng_others],
                ['全桁NG（見切れ）', ng_out],
                ['全桁NG（影）', ng_shadow],
                ['全桁NG（Occlusion）', ng_occlusion],
                ['全桁NG（FP）', ng_fp],
                ['全桁NG（Blur）', ng_blur],
                ['全桁NG（その他）', ng_others],
                ['GT不明', is_gt_unknown],
                ['再送回数', resend],
                ['全桁精度（メタごと）', detect_ok / detect_all],
                ['全桁精度（見切れ/FP抜き）', detect_ok / (detect_all - ng_fp - ng_out)]
            ])

    return path