from datetime import datetime, timezone, timedelta

# JST タイムゾーン定義
JST = timezone(timedelta(hours=9), name="JST")

def parse_timestamp(ts: str) -> datetime:
    """UTCフォーマット YYYYMMDDhhmmssSSS → JST datetime"""
    # UTCとしてパース
    dt_utc = datetime.strptime(ts[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    millis = int(ts[14:]) if len(ts) > 14 else 0
    dt_utc = dt_utc.replace(microsecond=millis * 1000)

    # JST に変換
    return dt_utc.astimezone(JST)

def format_jst(dt: datetime) -> str:
    """JST datetime を 'YYYY/MM/DD HH:MM:SS.mmm' 形式に変換"""
    return dt.strftime("%Y/%m/%d %H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}"

def diff_timestamp(ts1: str, ts2: str):
    """2つのUTC timestampを比較（表示はJST）"""
    dt1 = parse_timestamp(ts1)
    dt2 = parse_timestamp(ts2)
    diff = abs(dt2 - dt1)

    total_seconds = diff.total_seconds()
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    return hours, minutes, seconds

    # print(f"時刻1（JST）: {format_jst(dt1)}")
    # print(f"時刻2（JST）: {format_jst(dt2)}")
    print(f"差分: {int(hours)}時間 {int(minutes)}分 {seconds:.3f}秒")
    print(f"（合計 {total_seconds:.3f} 秒）")