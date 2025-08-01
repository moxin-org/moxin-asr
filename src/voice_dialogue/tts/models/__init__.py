"""
Models Module

TTS模型定义模块，包含：
- 基础配置抽象类
- 各种TTS引擎的配置模型
- 全局配置注册表
"""

from .base import (
    TTSConfigType,
    VoiceModelStatus,
    BaseTTSConfig,
    TTSConfigRegistry,
    tts_config_registry
)

# 导入具体的配置模型
try:
    from .moyoyo import MoYoYoTTSConfig

    _moyoyo_available = True
except ImportError:
    _moyoyo_available = False
    from voice_dialogue.utils.logger import logger

    logger.warning("MoYoYo TTS config not available")

try:
    from .kokoro import KokoroTTSConfig

    _kokoro_available = True
except ImportError:
    _kokoro_available = False
    from voice_dialogue.utils.logger import logger

    logger.warning("Kokoro TTS config not available")

# 动态构建导出列表
__all__ = [
    'TTSConfigType',
    'VoiceModelStatus',
    'BaseTTSConfig',
    'TTSConfigRegistry',
    'tts_config_registry',
]

if _moyoyo_available:
    __all__.append('MoYoYoTTSConfig')
if _kokoro_available:
    __all__.append('KokoroTTSConfig')


# 自动注册所有可用的配置
def _auto_register_configs():
    """自动注册所有TTS配置"""
    try:
        if _moyoyo_available:
            from ..configs.moyoyo import get_moyoyo_configs
            for config in get_moyoyo_configs():
                tts_config_registry.register_config(config)
    except Exception as e:
        from voice_dialogue.utils.logger import logger
        logger.error(f"Failed to auto-register configs: {e}")

    try:
        if _kokoro_available:
            from ..configs.kokoro import get_kokoro_configs
            for config in get_kokoro_configs():
                tts_config_registry.register_config(config)
    except Exception as e:
        from voice_dialogue.utils.logger import logger
        logger.error(f"Failed to auto-register configs: {e}")


# 模块加载时自动注册配置
_auto_register_configs()


# 配置统计信息
def get_config_stats():
    """获取配置统计信息"""
    all_configs = tts_config_registry.get_all_configs()
    stats = {
        'total_configs': len(all_configs),
        'configs_by_type': {}
    }

    for config_type in TTSConfigType:
        type_configs = tts_config_registry.get_configs_by_type(config_type)
        stats['configs_by_type'][config_type.value] = len(type_configs)

    return stats
