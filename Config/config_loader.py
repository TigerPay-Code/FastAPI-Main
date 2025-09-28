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
                    ['python_version', 'Python版本', '3.10.12']
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
                    ['interval', '任务间隔时间 (秒)', 1800]
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
            logger.info(f"开始初始化：{item[1]} ...")
            for sub_item in item[2]:
                public_config.set(key=f'{item[0]}.{sub_item[0]}', value=sub_item[2])
                if 'password' in sub_item[0]:
                    logger.info(f"设置配置：{item[0]}.{sub_item[0]} = {'*' * len(sub_item[2])}")
                else:
                    logger.info(f"设置配置：{item[0]}.{sub_item[0]} = {sub_item[2]}")

        public_config.save()
        logger.info(f"初始化配置成功！")

    except FileNotFoundError as init_file_error:
        logger.warning(f"错误：配置文件未找到，请检查路径。{init_file_error}")
    except Exception as init_error:
        logger.warning(f"初始化配置时发生错误：{init_error}")
