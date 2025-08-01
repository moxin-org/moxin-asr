from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np

from ..models.base import BaseTTSConfig


class TTSInterface(ABC):
    """TTS服务的抽象接口"""

    def __init__(self, config: BaseTTSConfig):
        self.config = config
        self._is_ready = False

    @abstractmethod
    def setup(self, **kwargs) -> None:
        """
        初始化TTS服务
        
        Args:
            **kwargs: 额外的初始化参数
        """
        pass

    @abstractmethod
    def warmup(self, warmup_steps: int = 1) -> None:
        """
        预热TTS引擎
        
        Args:
            warmup_steps: 预热步数
        """
        pass

    @abstractmethod
    def synthesize(self, text: str, **kwargs) -> Tuple[np.ndarray, int]:
        """
        将文本转换为语音
        
        Args:
            text: 要转换的文本
            **kwargs: 额外的合成参数
            
        Returns:
            Tuple[np.ndarray, int]: (音频数据, 采样率)
        """
        pass

    @property
    def is_ready(self) -> bool:
        """
        检查TTS服务是否准备就绪
        
        Returns:
            bool: 是否准备就绪
        """
        return self._is_ready

    @is_ready.setter
    def is_ready(self, value: bool):
        self._is_ready = value

    def get_config(self) -> BaseTTSConfig:
        """获取当前配置"""
        return self.config


class TTSFactory:
    """TTS工厂类，用于创建不同的TTS实现"""

    _registry = {}

    @classmethod
    def register(cls, provider_name: str, tts_class):
        """注册TTS提供者"""
        cls._registry[provider_name] = tts_class

    @classmethod
    def create(cls, config: BaseTTSConfig) -> TTSInterface:
        """
        根据配置创建TTS实例
        
        Args:
            config: TTS配置
            
        Returns:
            TTSInterface: TTS实例
            
        Raises:
            ValueError: 不支持的TTS提供者
        """
        provider = config.provider.value
        if provider not in cls._registry:
            raise ValueError(f"不支持的TTS提供者: {provider}")

        tts_class = cls._registry[provider]
        return tts_class(config)

    @classmethod
    def list_providers(cls):
        """列出所有已注册的TTS提供者"""
        return list(cls._registry.keys())
