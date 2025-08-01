"""
Runtime Module

TTS运行时模块，包含：
- TTS抽象接口定义
- TTS工厂类
- 具体TTS实现
"""

from .interface import TTSInterface, TTSFactory

__all__ = [
    'TTSInterface',
    'TTSFactory',
]

# 导入所有TTS实现，确保注册装饰器被执行
try:
    from .moyoyo import MoYoYoTTS

    __all__.append('MoYoYoTTS')
except ImportError as e:
    # 如果某些TTS实现无法导入，不影响整体功能
    from voice_dialogue.utils.logger import logger

    logger.warning(f"Failed to import some TTS implementations: {e}")

try:
    from .kokoro import KokoroTTS

    __all__.append('KokoroTTS')
except ImportError as e:
    # 如果某些TTS实现无法导入，不影响整体功能
    from voice_dialogue.utils.logger import logger

    logger.warning(f"Failed to import some TTS implementations: {e}")
