import os
import configparser
import sys

from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)


class ConfigLoader:
    """
    一个通用的配置文件加载器，支持 INI, JSON, YAML 格式。
    """

    def __init__(self, config_path):
        """
        初始化配置加载器。

        :param config_path: 配置文件的路径。
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        self.config_path = config_path
        self._config_data = self._load_config()

    def _load_config(self):
        """
        根据文件扩展名加载配置文件。
        """
        file_ext = os.path.splitext(self.config_path)[1].lower()
        if file_ext in ['.ini']:
            return self._load_ini()
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def _load_ini(self):
        """
        加载 INI 格式的配置文件。
        """
        config = configparser.ConfigParser()
        config.read(self.config_path, encoding='utf-8')
        data = {}
        for section in config.sections():
            data[section] = dict(config.items(section))
        return data

    def get(self, key, get_type: type = str, default=None):
        """
        通过点分隔的键路径获取配置值。

        :param key: 配置键，例如 'database.host'。
        :param get_type: 期望返回的数据类型，例如 str,int, float, bool。
        :param default: 如果键不存在，返回的默认值。
        :return: 配置值。
        """
        keys = key.split('.')
        value = self._config_data
        try:
            for k in keys:
                if isinstance(value, list) and k.isdigit():
                    value = value[int(k)]
                else:
                    value = value[k]
        except (KeyError, IndexError, TypeError):
            return default

        if get_type and value is not None:
            try:
                if get_type is bool:
                    return str(value).lower() in ('true', '1', 't', 'y')
                return get_type(value)  # 修正了这一行
            except (ValueError, TypeError):
                return default

        return value

    def set(self, key: str, value):
        """
        在内存中设置或修改配置值。

        :param key: 配置键，例如 'database.host'。
        :param value: 要设置的新值。
        """
        keys = key.split('.')
        current_level = self._config_data
        for k in keys[:-1]:
            # 将键转换为小写以匹配 ini 文件中的行为
            if isinstance(current_level, dict) and 'configparser' in sys.modules:
                k = k.lower()
            current_level = current_level.setdefault(k, {})

        # 将最后的键转换为小写以匹配 ini 文件中的行为
        last_key = keys[-1]
        if isinstance(current_level, dict) and 'configparser' in sys.modules:
            last_key = last_key.lower()

        current_level[last_key] = value

    def save(self):
        """
        将内存中的配置数据写回文件。
        """
        file_ext = os.path.splitext(self.config_path)[1].lower()
        if file_ext in ['.ini']:
            self._save_ini()
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def _save_ini(self):
        """
        将配置数据保存为 INI 格式。
        """
        config = configparser.ConfigParser()
        for section, items in self._config_data.items():
            config[section] = {k: str(v) for k, v in items.items()}

        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)


project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 构造配置文件路径
config_file = os.path.join(project_root, 'config.ini')

try:
    public_config = ConfigLoader(config_file)
except FileNotFoundError as e:
    logger.warning(f"错误：配置文件未找到，请检查路径。{e}")
    public_config = None
except Exception as e:
    logger.warning(f"初始化配置时发生错误：{e}")
    public_config = None


def initialize_config():
    """
    根据当前操作系统更新配置文件。
    """
    global public_config
    try:
        # 检测操作系统
        os_name = sys.platform
        system_name = "Unknown"

        if os_name.startswith('win'):
            system_name = "Windows"
        elif os_name.startswith('linux'):
            system_name = "Linux"
        elif os_name.startswith('darwin'):
            system_name = "macOS"

        con_data = [
            [
                'software', '软件配置',
                [
                    ['init', '初始化状态', True],
                    ['system', '操作系统', system_name],
                    ['app_name', '应用名称', 'FastAPI Receive Pay Notify Service'],
                    ['version', '版本号', '1.0.00'],
                    ['debug', '调试模式', False],
                    ['python_version', 'Python版本', '3.10.12'],
                    ['timezone', '本系统默认时区', 'Asia/Shanghai']
                ]
            ],

            [
                'hardware', '硬件配置',
                [
                    ['init', '初始化状态', True],
                    ['physical_cores', '物理核心数', 1],
                    ['logical_cores', '逻辑核心数', 2]
                ]
            ],

            [
                'database', '数据库配置',
                [
                    ['init', '初始化状态', True],
                    ['host', '数据库主机', '127.0.0.1'],
                    ['port', '数据库端口', 3306],
                    ['user', '数据库用户名', 'remote'],
                    ['password', '数据库密码', 'kb7$rL3d8!tQ'],
                    ['database', '数据库名称', 'fastapi'],
                    ['charset', '数据库字符集', 'utf8mb4'],
                    ['minsize', '数据库最小连接数', 5],
                    ['maxsize', '数据库最大连接数', 20],
                    ['pool_size', '数据库连接池大小', 10],
                    ['pool_recycle', '数据库连接池回收时间', 3600]
                ]
            ],

            [
                'redis', 'Redis配置',
                [
                    ['init', '初始化状态', True],
                    ['host', 'Redis主机', '127.0.0.1'],
                    ['port', 'Redis端口', 6379],
                    ['password', 'Redis密码', ''],
                    ['db', 'Redis数据库', 0],
                    ['max_connections', 'Redis最大连接数', 100],
                    ['redis_url', 'Redis连接URL', 'redis://127.0.0.1:6379/0'],
                    ['cache_expire', '缓存过期时间', 600]
                ]
            ],

            [
                'order', '订单配置',
                [
                    ['delay_seconds', '订单延迟时间', 60]
                ]
            ],

            [
                'task', '自动任务配置',
                [
                    ['interval', '检查未处理支付通知的时间间隔（秒）', 1800],


                    ['job1.enable', '定时任务开关', True],
                    ['job1.name', '定时任务名称', '工作日早上九点开始晚上8点结束，每隔半小时检查一次未处理支付通知'],
                    ['job1.trigger', '定时任务触发器', 'interval'],  # interval, cron, date

                    ['job1.year', '间隔年份', 1],
                    ['job1.month', '间隔月份', 1],
                    ['job1.weeks', '间隔周数', 1],
                    ['job1.days', '间隔天数', 1],
                    ['job1.hours', '间隔小时数', 1],
                    ['job1.minutes', '间隔分钟数', 30],
                    ['job1.seconds', '间隔秒数', 0],

                    ['job1.start_date', '定时任务开始时间', '2024-01-01 09:00:00'],
                    ['job1.end_date', '定时任务结束时间', '2030-12-31 23:59:59'],

                    ['job1.timezone', '定时任务时区', 'Asia/Shanghai'],

                    # day_of_week 完整名称：sunday, monday, tuesday, wednesday, thursday, friday, saturday
                    # day_of_week 简写名称：sun, mon, tue, wed, thu, fri, sat
                    # 每周一执行
                    # day_of_week = 'mon'

                    # 每周三和周五执行
                    # day_of_week = 'wed,fri'

                    # 工作日内执行（周一至周五）
                    # day_of_week = 'mon-fri'

                    # 周末执行（周六和周日）
                    # day_of_week = 'sat,sun'

                    # 工作日+周六（周一至周六）
                    # day_of_week = 'mon-sat'

                    # 特定组合：周一、周三、周五、周日
                    # day_of_week = 'mon,wed,fri,sun'

                    # 每隔一天执行（周一、周三、周五、周日）
                    # day_of_week = '*/2'  # 等价于 0,2,4,6

                    # 每三天执行一次（周一、周四）
                    # day_of_week = '*/3'  # 等价于 0,3,6

                    # 每月第一个周一
                    # day_of_week = 'mon#1'

                    # 每月最后一个周五
                    # day_of_week = 'fri#last'  # 或 'fri#-1'

                    # 所有工作日（周一至周五）
                    # day_of_week = 'mon-fri'  # 或 '1-5'

                    # 所有周末（周六至周日）
                    # day_of_week = 'sat-sun'  # 或 '6-7' 或 'weekend'

                    # 每周的每天
                    # day_of_week = '*' 或者忽略掉这个参数

                    ['job1.day_of_week', '定时任务星期几执行', 'mon-fri'],
                    ['job1.month', '定时任务月份', '*'],
                    ['job1.day', '定时任务日期', '*'],
                    ['job1.func', '定时任务函数', 'app.tasks.check_unprocessed_payment_notify'],
                    ['job1.args', '定时任务参数', ''],
                    ['job1.kwargs', '定时任务关键字参数', ''],
                    ['job1.trigger', '定时任务触发器', 'cron'],
                    ['job1.timezone', '定时任务时区', 'Asia/Shanghai'],
                    ['job1.misfire_grace_time', '定时任务容错时间', 300],
                    ['job1.coalesce', '定时任务合并任务', True],
                    ['job1.max_instances', '定时任务最大实例数', 1],
                    ['job1.replace_existing', '定时任务替换已存在任务', True]

                ]
            ],

            [
                'telegram', 'Telegram机器人配置',
                [
                    ['enable', '是否启用Telegram机器人', True],
                    ['token', '机器人Token', '8263751942:AAH5rvEopgKEERvUa9peWZ-TnctU230rHUU'],
                    ['chat_id', '默认聊天ID', 5312177749],
                    ['admin_chat_id', '管理员聊天ID', 5312177749]
                ]
            ]
        ]

        for item in con_data:
            logger.info(f"开始初始化：{item[1]}[{item[0]}] ...")
            for sub_item in item[2]:
                public_config.set(key=f'{item[0]}.{sub_item[0]}', value=sub_item[2])
                if 'password' in sub_item[0] or 'token' in sub_item[0]:
                    if sub_item[2] is None or sub_item[2] == '' or len(sub_item[2]) <= 0:
                        logger.info(f"设置配置：{sub_item[0]} = ****** [{sub_item[1]}]")
                    else:
                        logger.info(f"设置配置：{sub_item[0]} = {'*' * len(sub_item[2])} [{sub_item[1]}]")
                else:
                    logger.info(f"设置配置：{sub_item[0]} = {sub_item[2]} [{sub_item[1]}]")

        public_config.save()
        logger.info(f"初始化配置成功！")

    except FileNotFoundError as init_file_error:
        logger.warning(f"错误：配置文件未找到，请检查路径。{init_file_error}")
    except Exception as init_error:
        logger.warning(f"初始化配置时发生错误：{init_error}")
