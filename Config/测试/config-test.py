import os
import sys
from Config.config_loader import ConfigLoader

# 获取当前脚本的绝对路径，例如: E:\FastAPI-Main\Config\测试\config-test.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# 向上跳两级，找到项目根目录 (E:\FastAPI-Main)
project_root = os.path.dirname(os.path.dirname(current_dir))

# 将项目根目录添加到 Python 解释器路径
sys.path.append(project_root)

# 构造 config.ini 的绝对路径
config_file_path = os.path.join(project_root, 'Config', 'config.ini')

try:
    # 实例化 ConfigLoader 并加载配置文件
    ini_config = ConfigLoader(config_file_path)

    # 获取配置值
    db_init = ini_config.get(key='database.init', get_type=bool)
    db_host = ini_config.get(key='database.host', get_type=str)
    db_port = ini_config.get(key='database.port', get_type=int)
    db_user = ini_config.get(key='database.user', get_type=str)
    db_password = ini_config.get(key='database.password', get_type=str)
    db_database = ini_config.get(key='database.database', get_type=str)
    db_charset = ini_config.get(key='database.charset', get_type=str)

    if not ini_config.get(key='database.init', get_type=bool):
        print("正在初始化数据库...")
        print(f"数据库地址: {db_host}")
        print(f"数据库端口: {db_port}")
        print(f"数据库用户: {db_user}")
        print(f"数据库密码: {db_password}")
        print(f"数据库名称: {db_database}")
        print(f"数据库字符集: {db_charset}")
        async_database_url = f'mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset={db_charset}'
        print(f"数据库连接 URL: {async_database_url}")
        print("数据库初始化完成。")

        ini_config.set(key='database.database_url', value=async_database_url)

        ini_config.set(key='database.init', value=True)
        ini_config.save()
    else:
        print("数据库已经初始化。")
        async_database_url = ini_config.get(key='database.database_url', get_type=str)
        print(f"数据库连接 URL: {async_database_url}")
        ini_config.set(key='database.init', value=False)
        ini_config.save()




except FileNotFoundError as e:
    print(f"错误: {e}")
except Exception as e:
    print(f"发生其他错误: {e}")
