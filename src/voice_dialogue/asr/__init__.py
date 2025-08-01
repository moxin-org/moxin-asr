"""
ASR Module

提供自动语音识别(ASR)功能的完整解决方案，包括：
- ASR管理器和注册系统
- 多种ASR引擎支持
- 配置管理
- 运行时接口
"""

from .models import (
    ASRInterface,
)
from .manager import (
    ASRManager,
    ASRRegistryTables,
    asr_manager,
    asr_tables,
    register_all_asr
)

__version__ = "1.0.0"

__all__ = [
    # 管理器和注册表
    'ASRManager',
    'ASRRegistryTables',
    'asr_manager',
    'asr_tables',
    'register_all_asr',

    # 配置模型

    # 运行时接口
    'ASRInterface',
]

# 模块初始化时自动注册所有ASR实现
# register_all_asr() 已在 asr_manager 模块中自动调用 