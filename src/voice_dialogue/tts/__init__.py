"""
Audio Generator Module

提供文本转语音(TTS)功能的完整解决方案，包括：
- TTS管理器和注册系统
- 多种TTS引擎支持
- 配置管理
- 运行时接口
"""

from .models import (
    TTSConfigType,
    VoiceModelStatus,
    tts_config_registry,
    BaseTTSConfig
)
from .runtime import (
    TTSInterface,
    TTSFactory
)
from .manager import (
    TTSManager,
    TTSRegistryTables,
    tts_manager,
    tts_tables,
    register_all_tts
)

__version__ = "1.0.0"

__all__ = [
    # 管理器和注册表
    'TTSManager',
    'TTSRegistryTables',
    'tts_manager',
    'tts_tables',
    'register_all_tts',

    # 配置模型
    'TTSConfigType',
    'VoiceModelStatus',
    'tts_config_registry',
    'BaseTTSConfig',

    # 运行时接口
    'TTSInterface',
    'TTSFactory',
]

# 模块初始化时自动注册所有TTS实现
# register_all_tts() 已在 tts_manager 模块中自动调用
