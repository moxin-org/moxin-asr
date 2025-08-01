import re

import librosa
import numpy as np

from voice_dialogue.utils.logger import logger


def has_no_words(text: str) -> bool:
    """
    检查文本是否不包含任何单词（字母、数字或中文字符）。
    如果文本只包含标点、空格等符号，则返回 True。
    """
    if not text:
        return True
    # 搜索任何字母、数字或中文字符
    if re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]', text):
        return False
    return True


def normalize_audio_frame(data: bytes) -> 'np.ndarray':
    """
    将 int16 格式的音频字节数据转换为 [-1.0, 1.0] 范围的 numpy 浮点数组。
    """
    return np.frombuffer(data, dtype=np.int16).astype(np.float32) / np.iinfo(np.int16).max


def calculate_audio_duration(audio_data: 'np.ndarray', sample_rate: int = 16000) -> float:
    """
    计算音频时长（秒）。
    """
    try:
        return librosa.get_duration(y=audio_data, sr=sample_rate)
    except Exception as e:
        logger.error(f"计算音频时长时发生错误: {e}")
        return 0.0
