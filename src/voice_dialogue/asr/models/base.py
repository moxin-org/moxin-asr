from abc import ABC, abstractmethod
from enum import Enum

import librosa
import numpy as np

from voice_dialogue.config import paths


class ASRConfigType(Enum):
    """ASR引擎类型枚举"""
    FUNASR = 'funasr'
    WHISPER_CPP = 'whisper_cpp'


class Language(Enum):
    """支持的语言枚举"""
    AUTO = 'auto'
    CHINESE = 'zh'
    ENGLISH = 'en'


class ASRInterface(ABC):
    """ASR服务的抽象接口"""
    supported_langs = []

    def __init__(self):
        warmup_audiofile = paths.AUDIO_RESOURCES_PATH / 'jfk.flac'
        if warmup_audiofile.exists():
            audiodata, _ = librosa.load(warmup_audiofile, sr=16000, mono=True)
        else:
            # 创建测试音频
            audiodata = np.random.randn(16000).astype(np.float32) * 0.1  # 1秒的噪声
        self.warmup_audiodata = audiodata

    @abstractmethod
    def setup(self, **kwargs) -> None:
        """
        初始化ASR服务

        Args:
            **kwargs: 额外的初始化参数
        """
        pass

    @abstractmethod
    def warmup(self) -> None:
        """预热ASR引擎"""
        pass

    @abstractmethod
    def transcribe(self, audio_array: np.ndarray, language: str = None) -> str:
        """
        将音频转换为文本

        Args:
            audio_array: 音频数据
            language: 指定语言，如果为None则使用配置中的语言

        Returns:
            str: 识别结果文本
        """
        pass
