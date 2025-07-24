import sys
from loguru import logger

def setup_logger():
    """
    配置全局的loguru日志记录器。
    - 移除默认的处理器，以完全控制日志格式和输出。
    - 添加一个新的处理器，将日志输出到标准错误流(stderr)。
    - 日志级别设置为 "INFO"，意味着INFO级别及以上的日志(INFO, SUCCESS, WARNING, ERROR, CRITICAL)才会被显示。
    - 日志格式包含时间、级别、模块/函数/行号以及日志消息。
    """
    logger.remove()  # 移除默认配置
    logger.add(
        sys.stderr,
        level="INFO",  # 恢复标准的日志级别
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        colorize=True,
    )
    return logger

# 创建并导出一个预配置的logger实例
log = setup_logger() 