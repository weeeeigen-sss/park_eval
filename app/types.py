from enum import Enum
from PyQt6.QtCore import Qt

class Status(Enum):
    NoLabel = 0
    OK = 1
    NG_Out = 2
    NG_Shadow = 3
    NG_Occlusion = 4
    NG_FP = 5
    NG_Blur = 6
    NG_Others = 7
    OK_Out = 8
    Wrong_Out = 9
    NG_OverExposure = 10
    NG_AI = 11
    MovingIn = 12
    MovingOut = 13


key_status_map = {
    Qt.Key.Key_1: Status.OK,
    Qt.Key.Key_2: Status.NG_Out,
    Qt.Key.Key_3: Status.NG_Shadow,
    Qt.Key.Key_4: Status.NG_Occlusion,
    Qt.Key.Key_5: Status.NG_FP,
    Qt.Key.Key_6: Status.NG_Blur,
    Qt.Key.Key_7: Status.NG_OverExposure,
    Qt.Key.Key_8: Status.NG_AI,
    Qt.Key.Key_9: Status.NG_Others,
    Qt.Key.Key_0: Status.Wrong_Out,
}


def text_for(status: Status):
    if status == Status.NoLabel:
        return ''
    elif status == Status.OK:
        return 'OK'
    elif status == Status.NG_Out:
        return 'NG（見切れ）'
    elif status == Status.NG_Shadow:
        return 'NG（影）'
    elif status == Status.NG_Occlusion:
        return 'NG（Occlusion）'
    elif status == Status.NG_FP:
        return 'NG（FP）'
    elif status == Status.NG_Blur:
        return 'NG（ブラー）'
    elif status == Status.NG_Others:
        return 'NG（その他）'
    elif status == Status.OK_Out:
        return 'OK（出庫）'
    elif status == Status.Wrong_Out:
        return '誤出庫'
    elif status == Status.NG_OverExposure:
        return 'NG（白飛び）'
    elif status == Status.NG_AI:
        return 'NG（AIモデル）'
    elif status == Status.MovingIn:
        return 'Moving（入庫）'
    elif status == Status.MovingOut:
        return 'Moving（出庫）'
