import datetime
from zoneinfo import ZoneInfo
import time


def is_valid_timestamp(ts):
    """
    判断是否是有效的时间戳（正整数，且通常是10位或13位）
    :param ts: 时间戳（可以是整数或浮点数）
    :return: 如果是有效时间戳，返回 True；否则返回 False
    """
    if isinstance(ts, (int, float)) and ts > 0:
        ts_int = int(ts)
        return len(str(ts_int)) in [10, 13]
    return False


def get_sec_int_timestamp() -> int:  # 10位整数时间戳
    """
    获取当前时间的秒级时间戳（10位整数）
    :return: 秒级时间戳
    """
    return int(time.time())


def get_ms_int_timestamp() -> int:  # 13位整数时间戳
    """
    获取当前时间的毫秒级时间戳（13位整数）
    :return: 毫秒级时间戳
    """
    return int(time.time() * 1000)


def get_local_time_str(stamp=int(time.time())) -> str:  # 时间戳转换为本地时间字符串
    """
    将时间戳转换为本地时间字符串（支持秒级和毫秒级时间戳）
    :param stamp: 时间戳（秒级或毫秒级）
    :return: 本地时间字符串（格式：YYYY-MM-DD HH:MM:SS）
    """
    # 判断 stamp 是否有效
    if not is_valid_timestamp(stamp):
        # 若无效，使用当前时间戳（比如通过 get_sec_int_timestamp()）
        timestamp_to_use = get_sec_int_timestamp()
    else:
        # 若有效，判断是否为毫秒级（13位），是则转秒级
        timestamp_to_use = int(stamp / 1000) if len(str(stamp)) == 13 else stamp

    # 统一转为本地时间字符串
    return str(datetime.datetime.fromtimestamp(timestamp_to_use))

