import os
import sys

# 获取项目根目录，以便正确导入模块和找到配置文件
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 导入 ConfigLoader
from Config.config_loader import ConfigLoader

# 构造配置文件路径
config_path = os.path.join(project_root,  'config.ini')


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
            print(f"检测到系统名称不匹配：当前为 '{system_name}'，配置文件为 '{current_system}'")
            print("正在更新配置文件...")

            # 使用 set 方法更新值
            config.set('SoftWare.system', system_name)

            # 保存更改到文件
            config.save()
            print("配置文件已更新。")
        else:
            print(f"配置文件已是最新状态，系统名称为 '{system_name}'。")

    except FileNotFoundError as e:
        print(f"错误：配置文件未找到，请检查路径。{e}")
    except Exception as e:
        print(f"初始化配置时发生错误：{e}")


# 运行初始化函数
if __name__ == "__main__":
    initialize_config()