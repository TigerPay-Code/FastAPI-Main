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


def get_time_in_timezone(stamp=int(time.time()), timezone="UTC") -> str:
    """
    将时间戳转换为指定时区的时间字符串
    :param stamp: 时间戳（秒级或毫秒级）
    :param timezone: 时区名称，默认为UTC
    :return: 指定时区的时间字符串（格式：YYYY-MM-DD HH:MM:SS %Z%z）
    """
    # 扩展时区映射表
    timezone_map = {
        # 亚洲
        "beijing": "Asia/Shanghai",  # 北京时间
        "china": "Asia/Shanghai",  # 中国时间
        "shanghai": "Asia/Shanghai",  # 上海时间
        "hongkong": "Asia/Hong_Kong",  # 香港时间
        "taipei": "Asia/Taipei",  # 台北时间
        "tokyo": "Asia/Tokyo",  # 东京时间
        "seoul": "Asia/Seoul",  # 首尔时间
        "singapore": "Asia/Singapore",  # 新加坡时间
        "bangkok": "Asia/Bangkok",  # 曼谷时间
        "kualalumpur": "Asia/Kuala_Lumpur",  # 吉隆坡时间
        "jakarta": "Asia/Jakarta",  # 雅加达时间
        "manila": "Asia/Manila",  # 马尼拉时间
        "hanoi": "Asia/Ho_Chi_Minh",  # 河内时间
        "dhaka": "Asia/Dhaka",  # 达卡时间
        "kolkata": "Asia/Kolkata",  # 加尔各答时间（印度标准时间）
        "mumbai": "Asia/Kolkata",  # 孟买时间
        "delhi": "Asia/Kolkata",  # 德里时间
        "dubai": "Asia/Dubai",  # 迪拜时间
        "riyadh": "Asia/Riyadh",  # 利雅得时间
        "tehran": "Asia/Tehran",  # 德黑兰时间
        "baghdad": "Asia/Baghdad",  # 巴格达时间

        # 欧洲
        "london": "Europe/London",  # 伦敦时间
        "paris": "Europe/Paris",  # 巴黎时间
        "berlin": "Europe/Berlin",  # 柏林时间
        "rome": "Europe/Rome",  # 罗马时间
        "madrid": "Europe/Madrid",  # 马德里时间
        "amsterdam": "Europe/Amsterdam",  # 阿姆斯特丹时间
        "brussels": "Europe/Brussels",  # 布鲁塞尔时间
        "vienna": "Europe/Vienna",  # 维也纳时间
        "zurich": "Europe/Zurich",  # 苏黎世时间
        "stockholm": "Europe/Stockholm",  # 斯德哥尔摩时间
        "oslo": "Europe/Oslo",  # 奥斯陆时间
        "copenhagen": "Europe/Copenhagen",  # 哥本哈根时间
        "helsinki": "Europe/Helsinki",  # 赫尔辛基时间
        "warsaw": "Europe/Warsaw",  # 华沙时间
        "prague": "Europe/Prague",  # 布拉格时间
        "budapest": "Europe/Budapest",  # 布达佩斯时间
        "moscow": "Europe/Moscow",  # 莫斯科时间
        "athens": "Europe/Athens",  # 雅典时间
        "lisbon": "Europe/Lisbon",  # 里斯本时间
        "dublin": "Europe/Dublin",  # 都柏林时间

        # 北美
        "newyork": "America/New_York",  # 纽约时间
        "losangeles": "America/Los_Angeles",  # 洛杉矶时间
        "chicago": "America/Chicago",  # 芝加哥时间
        "toronto": "America/Toronto",  # 多伦多时间
        "vancouver": "America/Vancouver",  # 温哥华时间
        "miami": "America/New_York",  # 迈阿密时间（与纽约相同）
        "washington": "America/New_York",  # 华盛顿时间（与纽约相同）
        "boston": "America/New_York",  # 波士顿时间（与纽约相同）
        "detroit": "America/Detroit",  # 底特律时间
        "houston": "America/Chicago",  # 休斯顿时间（与芝加哥相同）
        "phoenix": "America/Phoenix",  # 凤凰城时间
        "denver": "America/Denver",  # 丹佛时间
        "dallas": "America/Chicago",  # 达拉斯时间（与芝加哥相同）
        "seattle": "America/Los_Angeles",  # 西雅图时间（与洛杉矶相同）
        "sanfrancisco": "America/Los_Angeles",  # 旧金山时间（与洛杉矶相同）
        "lasvegas": "America/Los_Angeles",  # 拉斯维加斯时间（与洛杉矶相同）

        # 南美
        "saopaulo": "America/Sao_Paulo",  # 圣保罗时间
        "riodejaneiro": "America/Sao_Paulo",  # 里约热内卢时间
        "buenosaires": "America/Argentina/Buenos_Aires",  # 布宜诺斯艾利斯时间
        "lima": "America/Lima",  # 利马时间
        "bogota": "America/Bogota",  # 波哥大时间
        "santiago": "America/Santiago",  # 圣地亚哥时间
        "caracas": "America/Caracas",  # 加拉加斯时间

        # 非洲
        "cairo": "Africa/Cairo",  # 开罗时间
        "johannesburg": "Africa/Johannesburg",  # 约翰内斯堡时间
        "nairobi": "Africa/Nairobi",  # 内罗毕时间
        "lagos": "Africa/Lagos",  # 拉各斯时间
        "casablanca": "Africa/Casablanca",  # 卡萨布兰卡时间
        "tunis": "Africa/Tunis",  # 突尼斯时间
        "algiers": "Africa/Algiers",  # 阿尔及尔时间

        # 大洋洲
        "sydney": "Australia/Sydney",  # 悉尼时间
        "melbourne": "Australia/Melbourne",  # 墨尔本时间
        "brisbane": "Australia/Brisbane",  # 布里斯班时间
        "perth": "Australia/Perth",  # 珀斯时间
        "auckland": "Pacific/Auckland",  # 奥克兰时间
        "wellington": "Pacific/Auckland",  # 惠灵顿时间（与奥克兰相同）
        "fiji": "Pacific/Fiji",  # 斐济时间
        "honolulu": "Pacific/Honolulu",  # 檀香山时间

        # 其他
        "utc": "UTC",  # UTC时间
        "gmt": "GMT",  # GMT时间
    }

    # 获取时区对象
    tz_key = timezone.lower()
    tz_str = timezone_map.get(tz_key, timezone)

    try:
        tz = ZoneInfo(tz_str)
    except:
        # 如果时区无效，使用UTC
        tz = ZoneInfo("UTC")

    # 判断 stamp 是否有效
    if not is_valid_timestamp(stamp):
        # 若无效，使用当前时间戳
        timestamp_to_use = get_sec_int_timestamp()
    else:
        # 若有效，判断是否为毫秒级（13位），是则转秒级
        timestamp_to_use = int(stamp / 1000) if len(str(stamp)) == 13 else stamp

    # 创建UTC时间
    utc_time = datetime.datetime.fromtimestamp(timestamp_to_use, tz=ZoneInfo("UTC"))

    # 转换为目标时区时间
    target_time = utc_time.astimezone(tz)

    # 格式化为字符串
    # return target_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    return target_time.strftime("%Y-%m-%d %H:%M:%S")


# cc = get_sec_int_timestamp()
# print(cc)
# print(f"当前时间戳: {cc}")
# print(f"北京时间: {get_time_in_timezone(cc, 'beijing')}")
# print(f"纽约时间: {get_time_in_timezone(cc, 'newyork')}")
# print(f"伦敦时间: {get_time_in_timezone(cc, 'london')}")
# print(f"东京时间: {get_time_in_timezone(cc, 'tokyo')}")
# print(f"悉尼时间: {get_time_in_timezone(cc, 'sydney')}")
# print(f"迪拜时间: {get_time_in_timezone(cc, 'dubai')}")
# print(f"莫斯科时间: {get_time_in_timezone(cc, 'moscow')}")
# print(f"巴黎时间: {get_time_in_timezone(cc, 'paris')}")
# print(f"柏林时间: {get_time_in_timezone(cc, 'berlin')}")
# print(f"新加坡时间: {get_time_in_timezone(cc, 'singapore')}")
# print(f"印度时间: {get_time_in_timezone(cc, 'kolkata')}")
# print(f"巴西时间: {get_time_in_timezone(cc, 'saopaulo')}")