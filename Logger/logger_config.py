import os
import logging
from logging.handlers import RotatingFileHandler

# 定义项目根目录，这里是 /data/FastAPI-Main
PROJECT_ROOT = "/data/FastAPI-Main"

# 定义集中的日志目录
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 确保日志目录存在，如果不存在则创建
# exist_ok=True 表示如果目录已存在，则不会抛出异常
os.makedirs(LOGS_DIR, exist_ok=True)

# 定义日志格式
LOG_FORMAT = "%(asctime)s %(levelname)s [%(process)d] - %(name)s - %(message)s"


def setup_logger(logger_name: str = None):
    """
    配置并返回一个专用于应用程序的日志记录器。
    """
    app_logger = logging.getLogger(logger_name)  # 可以用目录名作为logger的名称
    app_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, f"{logger_name}.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)

    if not app_logger.handlers:
        app_logger.addHandler(file_handler)

    return app_logger
