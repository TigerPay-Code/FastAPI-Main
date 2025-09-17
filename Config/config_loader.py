import os
import json
import configparser
import sys

import yaml
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
        elif file_ext in ['.json']:
            return self._load_json()
        elif file_ext in ['.yaml', '.yml']:
            return self._load_yaml()
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def _load_ini(self):
        """
        加载 INI 格式的配置文件。
        """
        config = configparser.ConfigParser()
        config.read(self.config_path)
        data = {}
        for section in config.sections():
            data[section] = dict(config.items(section))
        return data

    def _load_json(self):
        """
        加载 JSON 格式的配置文件。
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_yaml(self):
        """
        加载 YAML 格式的配置文件。
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            # 使用 FullLoader 以避免安全问题
            return yaml.load(f, Loader=yaml.FullLoader)

    def get(self, key, get_type: type = str, default=None):
        """
        通过点分隔的键路径获取配置值。

        :param key: 配置键，例如 'database.host'。
        :param get_type: 期望返回的数据类型，例如 int, float, bool。
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
        elif file_ext in ['.json']:
            self._save_json()
        elif file_ext in ['.yaml', '.yml']:
            self._save_yaml()
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

    def _save_json(self):
        """
        将配置数据保存为 JSON 格式。
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config_data, f, indent=4, ensure_ascii=False)

    def _save_yaml(self):
        """
        将配置数据保存为 YAML 格式。
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)


project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 构造配置文件路径
config_path = os.path.join(project_root, 'config.ini')


def initialize_config():
    """
    根据当前操作系统更新配置文件。
    """
    try:
        # 实例化 ConfigLoader 并加载配置文件
        config = ConfigLoader(config_path)

        # 检测操作系统
        os_name = sys.platform
        system_name = "Unknown"

        if os_name.startswith('win'):
            system_name = "Windows"
        elif os_name.startswith('linux'):
            system_name = "Linux"
        elif os_name.startswith('darwin'):
            system_name = "macOS"

        # 获取当前配置文件中的系统名称
        current_system = config.get('software.system')

        # 如果配置文件中的系统名称与当前系统不匹配，则进行更新
        if current_system != system_name:
            logger.warning(f"检测到系统名称不匹配：当前为 '{system_name}'，配置文件为 '{current_system}'")
            logger.warning("正在更新配置文件...")

            # 使用 set 方法更新值
            config.set('software.system', system_name)

            # 保存更改到文件
            config.save()
            logger.warning("配置文件已更新。")
        else:
            logger.warning(f"配置文件已是最新状态，系统名称为 '{system_name}'。")

    except FileNotFoundError as e:
        logger.warning(f"错误：配置文件未找到，请检查路径。{e}")
    except Exception as e:
        logger.warning(f"初始化配置时发生错误：{e}")
