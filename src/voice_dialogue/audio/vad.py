from typing import Optional

import numpy as np
import torch
from silero_vad import load_silero_vad

from voice_dialogue.utils.logger import logger


class SileroVAD:
    """
    一个线程安全的、基于单例模式的Silero VAD模型包装器。

    该类在首次实例化时加载 Silero VAD 模型，并提供一个方法来检测音频帧中的语音活动。
    设计为单例可以避免在应用中重复加载这个较为消耗资源模型。
    """
    _instance: Optional['SileroVAD'] = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, threshold: float = 0.7):
        """
        初始化 Silero VAD 模型。模型只会在首次创建实例时加载。

        Args:
            threshold (float): 用于判定语音活动的置信度阈值 (范围 0.0 到 1.0)。
        """
        if self._model is None:
            logger.info("正在首次初始化 Silero VAD 模型...")
            try:
                self._model = load_silero_vad()
                self._model.reset_states()
                self.threshold = threshold
                logger.info("Silero VAD 模型初始化成功。")
            except Exception as e:
                logger.error(f"初始化 Silero VAD 模型失败: {e}", exc_info=True)
                # 如果失败，重置实例，以便下次可以重试
                SileroVAD._instance = None
                raise

    def is_voice_active(self, audio_frame: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        检测给定的音频帧中是否包含语音活动。

        Args:
            audio_frame (np.ndarray): 一个一维的 float32 numpy 数组，代表音频数据。
                                      其数值范围应为 [-1.0, 1.0]。
                                      对于16kHz采样率，帧大小必须为 [512, 1024, 1536] 之一。
            sample_rate (int): 音频的采样率，必须是 8000 或 16000。

        Returns:
            bool: 如果检测到语音活动，返回 True，否则返回 False。
        """
        if self._model is None:
            logger.error("VAD 模型未初始化，无法执行检测。")
            return False

        if not isinstance(audio_frame, np.ndarray):
            logger.warning("VAD 检测的输入必须是一个 numpy 数组。")
            return False

        # Silero VAD 模型要求 float32 类型
        if audio_frame.dtype != np.float32:
            audio_frame = audio_frame.astype(np.float32)

        window_size = 512 if sample_rate == 16000 else 256

        audio_tensor = torch.from_numpy(audio_frame)

        try:
            probs = []
            for i in range(0, len(audio_tensor), window_size):
                audio_slice = audio_tensor[i:i + window_size]
                if len(audio_slice) < window_size:
                    audio_slice = audio_tensor[-window_size:]

                # 模型会返回一个包含语音可能性的张量
                prob = self._model(audio_slice, sample_rate).item()
                probs.append(prob)

            return any(prob >= self.threshold for prob in probs)
        except Exception as e:
            logger.error(f"VAD 检测过程中发生错误: {e}")
            return False
