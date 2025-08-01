"""
Configs Module

TTS配置模块，包含：
- 各种TTS引擎的预配置
- 配置加载函数
"""

# 导入配置加载函数
try:
    from .moyoyo import get_moyoyo_configs

    __all__ = [
        'get_moyoyo_configs',
    ]

    # 配置获取函数映射
    CONFIG_GETTERS = {
        'moyoyo': get_moyoyo_configs,
    }

except ImportError as e:
    from voice_dialogue.utils.logger import logger

    logger.warning(f"Failed to import some config modules: {e}")
    __all__ = []
    CONFIG_GETTERS = {}


def get_all_configs():
    """获取所有可用的TTS配置"""
    all_configs = []
    for getter_func in CONFIG_GETTERS.values():
        try:
            configs = getter_func()
            all_configs.extend(configs)
        except Exception as e:
            from voice_dialogue.utils.logger import logger
            logger.error(f"Failed to load configs from {getter_func.__name__}: {e}")
    return all_configs


def get_configs_by_type(tts_type: str):
    """根据TTS类型获取配置"""
    if tts_type in CONFIG_GETTERS:
        try:
            return CONFIG_GETTERS[tts_type]()
        except Exception as e:
            from voice_dialogue.utils.logger import logger
            logger.error(f"Failed to load configs for {tts_type}: {e}")
            return []
    return []
