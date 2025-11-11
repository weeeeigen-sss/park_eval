from enum import Enum

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