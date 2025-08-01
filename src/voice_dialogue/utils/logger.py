import sys

from loguru import logger as _logger

__all__ = ("logger",)


def setup_logger(
        level: str = "INFO",
        log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
) -> object:
    """
    Configure and return a loguru logger with console output only.

    Args:
        level: 日志级别 (INFO, DEBUG, WARNING, ERROR, CRITICAL)
        log_format: 日志格式字符串

    Returns:
        loguru.logger: 配置好的logger实例
    """
    # 移除所有现有的处理器
    _logger.remove()

    # 添加控制台处理器
    _logger.add(
        sys.stdout,
        level=level.upper(),
        format=log_format,
        colorize=True,
        enqueue=True  # 使日志线程安全
    )

    return _logger


logger = setup_logger()
