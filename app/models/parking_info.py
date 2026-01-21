import os
import json
import regex

from app.types import Status

class ParkingInfo:
    def __init__(self, info: dict, data: dict, json_path: str, lot: str = "", is_ps: bool = False):
        self.lot = lot
        self.is_ps = is_ps

        self.parse_info(info, data, json_path)

    @classmethod
    def create(cls, json_path, min_x=0, min_y=0, max_x=0, max_y=0):
        split = os.path.splitext(os.path.basename(json_path))[0].split('_')

        # For ebsim
        if len(split) < 2:
            lot = "ebsim"
            is_ps = False
        else:
            lot = split[1]
            is_ps = len(split) == 3

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            # For ebsim
            if lot == "ebsim":
                results = data["Inference_Results"]

                parking_gate_info = None
                best_score = 0

                for info in results:
                    tmp = info.get("parking_gate_info", {})
                    bbox = tmp.get("LPD_Bbox", {})
                    xmin = bbox.get("xmin", 0)
                    ymin = bbox.get("ymin", 0)
                    xmax = bbox.get("xmax", 0)
                    ymax = bbox.get("ymax", 0)
                    score = bbox.get("score", 0)

                    if xmin >= min_x and ymin >= min_y and xmax <= max_x and ymax <= max_y:
                        if score > best_score:
                            parking_gate_info = tmp
                        best_score = score

                    if parking_gate_info is not None:
                        return ParkingInfo(parking_gate_info, data, json_path)
                    else:
                        return None
            else:
                parking_lot_info = data["Inference_Results"][0]["parking_lot_info"]
                for info in parking_lot_info:
                    if info["Lot"] != lot:
                        continue
                    return ParkingInfo(info, data, json_path, lot, is_ps)

    def parse_info(self, info: dict, data: dict, json_path: str):
        self.json_data = data
        self.timestamp = str(info.get("TimeStamp"))
        self.json_path = json_path
        self.json_file = os.path.basename(json_path)

        self.is_occupied = info.get("Is_Occupied")
        self.is_occlusion = info.get("Is_Occlusion")
        self.is_uncertain = info.get("Is_Uncertain")
        self.vehicle_status = info.get("Vehicle_Status")

        plate_number = info.get("Plate_Number", {})
        self.lpr_top = plate_number.get("Top")
        self.top_quality = plate_number.get("Top_Quality")
        self.lpr_bottom = plate_number.get("Bottom")
        self.bottom_quality = plate_number.get("Bottom_Quality")

        self.plate_confidence = info.get("Plate_Confidence")

        lpd_bbox = info.get("LPD_Bbox", {})
        self.plate_xmin = lpd_bbox.get("xmin")
        self.plate_ymin = lpd_bbox.get("ymin")
        self.plate_xmax = lpd_bbox.get("xmax")
        self.plate_ymax = lpd_bbox.get("ymax")
        self.plate_width = lpd_bbox.get("width")
        self.plate_height = lpd_bbox.get("height")
        self.plate_score = lpd_bbox.get("score")

        vehicle_bbox = info.get("Vehicle_Bbox", {})
        self.vehicle_xmin = vehicle_bbox.get("xmin")
        self.vehicle_ymin = vehicle_bbox.get("ymin")
        self.vehicle_xmax = vehicle_bbox.get("xmax")
        self.vehicle_ymax = vehicle_bbox.get("ymax")
        self.vehicle_wdith = vehicle_bbox.get("width")
        self.vehicle_height = vehicle_bbox.get("height")
        self.vehicle_score = vehicle_bbox.get("score")

        duration = info.get("Duration", {})
        self.plate_count = duration.get("plate_count")
        self.vehicle_count = duration.get("vehicle_count")

        # For movement eval
        movement = info.get("Movement", {})
        plate = movement.get("Plate", {})
        end = plate.get("End", {})
        self.move_plate_end_y = end.get("y")
        self.stop_info:ParkingInfo = None


        self.status = Status.NoLabel
        self.is_miss_in = False
        self.is_miss_out = False
        self.is_gt_unknown = False
        self.is_first = False


    def name(self):
        name = self.timestamp + '_' + self.lot
        return name + '_ps' if self.is_ps else name
    
    def set(self, status: Status):
        self.status = status

    def set_stop_info(self, stop_info):
        self.stop_info = stop_info

    def set_miss_in(self, miss_in):
        self.is_miss_in = miss_in

    def set_miss_out(self, miss_out):
        self.is_miss_out = miss_out

    def set_gt_unknown(self, gt_unknown):
        self.is_gt_unknown = gt_unknown

    def set_is_first(self, first_park):
        self.is_first = first_park

    def is_conf_ng(self, threshold=0.3):
        if self.plate_confidence is not None and self.vehicle_status == 'Moving' and self.plate_confidence < threshold:
            return True
        return False
    
    def is_top_format_ng(self):
        if self.vehicle_status == 'Stop':
            if self.lpr_top is None:
                return True
        
            top_format = '^((\p{Han}{1,4}|\p{Hiragana}{3}|(\p{Han}|\p{Katakana}){3})([1-8][0-9A-Z]{2}|[0-9]{2}))$'
            top_match = regex.match(top_format, self.lpr_top)
            if top_match is None:
                return True
        return False
    
    def is_bottom_format_ng(self):
        if self.vehicle_status == 'Stop':         
            if self.lpr_bottom is None:
                return True
            
            bottom_format = '^(\p{Hiragana}|[YABEHKMT])([1-9]{1}\d{1}-\d{2}|・[1-9]{1}\d{2}|・{2}[1-9]{1}\d{1}|・{3}[1-9]{1})$'
            bottom_match = regex.match(bottom_format, self.lpr_bottom)
            if bottom_match is None:
                return True
            
        return False
    
    def diff_move_y(self):
        if self.status != Status.MovingOut or self.stop_info is None :
            return None
        
        return self.move_plate_end_y - self.stop_info.move_plate_end_y
    
    def is_move_y_ng(self, threshold=0):
        if self.status != Status.MovingOut:
            return False
        
        diff_y = self.diff_move_y()
        if diff_y is not None and diff_y > threshold:
            return True
    
        return False
