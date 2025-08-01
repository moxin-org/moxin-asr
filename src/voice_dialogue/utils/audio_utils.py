import numpy as np


def calculate_audio_duration(audio_data: np.ndarray, sample_rate: int) -> float:
    """
    计算音频数据的时长（秒）。

    Args:
        audio_data (np.ndarray): 音频数据数组。
        sample_rate (int): 采样率。

    Returns:
        float: 音频时长（秒）。
    """
    if audio_data is None or sample_rate == 0:
        return 0.0
    return len(audio_data) / sample_rate
