import logging
from logging.handlers import RotatingFileHandler

# 定义日志格式
# asctime: 记录时间, levelname: 级别名称, process: 进程ID, name: 日志记录器名称, message: 消息内容
LOG_FORMAT = "%(asctime)s %(levelname)s [%(process)d] - %(name)s - %(message)s"

# 定义文件路径
LOG_FILE_PATH = "/data/FastAPI-Main/ReceiveNotify/log/app.log"

def setup_logger():
    """
    配置并返回一个专用于应用程序的日志记录器。
    """
    # 创建一个日志记录器实例
    # app_logger 是我们自定义的记录器，区别于 Uvicorn 等默认记录器
    app_logger = logging.getLogger("app_logger")
    app_logger.setLevel(logging.INFO)  # 设置默认的日志级别

    # 创建一个文件处理器，用于将日志写入文件
    # RotatingFileHandler: 实现了日志文件的轮换，防止文件过大
    # maxBytes: 单个文件最大尺寸（这里是 100MB）
    # backupCount: 保留的日志文件个数（这里保留 5 个旧文件）
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=100 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )

    # 创建一个格式化器并将其添加到处理器
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    if not app_logger.handlers: # 确保只添加一次处理器
        app_logger.addHandler(file_handler)

    return app_logger

# 在这里直接调用函数来创建并导出全局可用的日志对象
# 这样在其他文件中只需要导入这个对象即可
logger = setup_logger()