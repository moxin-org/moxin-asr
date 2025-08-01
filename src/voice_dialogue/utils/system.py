"""系统相关工具函数"""

import locale
import os
import platform
from typing import Literal

__all__ = ('get_system_language', 'get_system_info', 'is_apple_silicon')


def get_system_language() -> Literal['zh', 'en']:
    """
    获取系统当前语言设置
    
    Returns:
        str: 返回 'zh' 或 'en'，默认为 'zh'
    """
    try:
        # 首先尝试从环境变量获取
        lang = os.environ.get('LANG', '')
        if not lang:
            lang = os.environ.get('LANGUAGE', '')
        if not lang:
            lang = os.environ.get('LC_ALL', '')
        if not lang:
            lang = os.environ.get('LC_MESSAGES', '')

        # 如果环境变量为空，尝试使用locale模块
        if not lang:
            try:
                lang, _ = locale.getdefaultlocale()
                if not lang:
                    lang = locale.getlocale()[0]
            except (ValueError, AttributeError):
                lang = None

        # 解析语言代码
        if lang:
            lang = lang.lower()
            if 'zh' in lang or 'chinese' in lang:
                return 'zh'
            elif 'en' in lang or 'english' in lang:
                return 'en'

    except Exception:
        pass
        # 如果所有方法都失败，返回默认值

    # 默认返回中文
    return 'zh'


def is_apple_silicon() -> bool:
    """
    检查当前系统是否为Apple Silicon
    
    Returns:
        bool: 如果是Apple Silicon返回True，否则返回False
    """
    return (platform.system() == 'Darwin' and
            platform.machine() in ('arm64', 'arm64e'))


def get_system_info() -> dict:
    """
    获取系统信息
    
    Returns:
        dict: 包含系统信息的字典
    """
    info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'machine': platform.machine(),
        'processor': platform.processor(),
        'language': get_system_language(),
        'python_version': platform.python_version(),
        'is_apple_silicon': is_apple_silicon(),
    }

    return info
