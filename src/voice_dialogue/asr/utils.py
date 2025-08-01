"""
ASR模块的工具函数
包含音频预处理、格式转换等工具函数
"""

import numpy as np


def ensure_minimum_audio_duration(
        audio_array: np.ndarray, min_duration: float = 1.0, sample_rate: int = 16000
) -> np.ndarray:
    """
    确保音频数组满足最小时长要求，如果不足则用静音填充

    Args:
        audio_array: 输入音频数组
        min_duration: 最小时长要求（秒），默认1秒
        sample_rate: 采样率，默认16000Hz

    Returns:
        处理后的音频数组
    """
    audio_duration = audio_array.shape[-1] / sample_rate

    if audio_duration < min_duration:
        padding_seconds = min_duration - audio_duration
        audio_array = padding_silence(audio_array, padding_seconds, sample_rate)

    return audio_array


def padding_silence(
        audio_data: np.ndarray, duration_seconds: float, sample_rate: int = 16000
) -> np.ndarray:
    """
    为音频数据添加静音填充

    Args:
        audio_data: 原始音频数据
        duration_seconds: 需要填充的时长（秒）
        sample_rate: 采样率

    Returns:
        填充后的音频数据
    """
    frequency = 440.0
    duration = duration_seconds + 0.1
    t = np.linspace(
        0, duration, int(sample_rate * duration), endpoint=False, dtype=audio_data.dtype
    )
    silence = 0.5 * np.sin(2 * np.pi * frequency * t)
    audio_data = np.concatenate([audio_data, silence])
    return audio_data


def validate_audio_array(audio_array: np.ndarray) -> bool:
    """
    验证音频数组是否有效

    Args:
        audio_array: 音频数组

    Returns:
        bool: 是否为有效的音频数组
    """
    if audio_array is None:
        return False

    if not isinstance(audio_array, np.ndarray):
        return False

    if audio_array.size == 0:
        return False

    if len(audio_array.shape) > 2:
        return False

    return True


def normalize_audio(audio_array: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """
    标准化音频数组的音量

    Args:
        audio_array: 输入音频数组
        target_peak: 目标峰值，默认0.95

    Returns:
        标准化后的音频数组
    """
    if not validate_audio_array(audio_array):
        raise ValueError("Invalid audio array")

    # 获取当前峰值
    current_peak = np.max(np.abs(audio_array))

    if current_peak == 0:
        return audio_array

    # 计算缩放因子
    scale_factor = target_peak / current_peak

    # 应用缩放
    normalized_audio = audio_array * scale_factor

    return normalized_audio


def convert_sample_rate(
        audio_array: np.ndarray,
        source_rate: int,
        target_rate: int
) -> np.ndarray:
    """
    转换音频采样率
    
    Args:
        audio_array: 输入音频数组
        source_rate: 源采样率
        target_rate: 目标采样率
    
    Returns:
        转换后的音频数组
    """
    if source_rate == target_rate:
        return audio_array

    try:
        import librosa
        return librosa.resample(audio_array, orig_sr=source_rate, target_sr=target_rate)
    except ImportError:
        # 如果没有librosa，使用简单的重采样
        ratio = target_rate / source_rate
        new_length = int(len(audio_array) * ratio)
        indices = np.linspace(0, len(audio_array) - 1, new_length)
        return np.interp(indices, np.arange(len(audio_array)), audio_array)


def trim_silence(
        audio_array: np.ndarray,
        threshold: float = 0.01,
        sample_rate: int = 16000
) -> np.ndarray:
    """
    修剪音频开头和结尾的静音部分
    
    Args:
        audio_array: 输入音频数组
        threshold: 静音检测阈值
        sample_rate: 采样率
    
    Returns:
        修剪后的音频数组
    """
    if not validate_audio_array(audio_array):
        return audio_array

    # 计算音频的绝对值
    audio_abs = np.abs(audio_array)

    # 找到非静音部分的开始和结束
    non_silent = audio_abs > threshold

    if not np.any(non_silent):
        # 如果全是静音，返回最小长度的音频
        min_samples = int(0.1 * sample_rate)  # 100ms
        return audio_array[:min_samples] if len(audio_array) > min_samples else audio_array

    # 找到第一个和最后一个非静音样本
    start_idx = np.argmax(non_silent)
    end_idx = len(non_silent) - np.argmax(non_silent[::-1])

    return audio_array[start_idx:end_idx]


def get_audio_duration(audio_array: np.ndarray, sample_rate: int = 16000) -> float:
    """
    获取音频时长（秒）
    
    Args:
        audio_array: 音频数组
        sample_rate: 采样率
    
    Returns:
        音频时长（秒）
    """
    if not validate_audio_array(audio_array):
        return 0.0

    return audio_array.shape[-1] / sample_rate


def create_silence(duration_seconds: float, sample_rate: int = 16000) -> np.ndarray:
    """
    创建指定时长的静音
    
    Args:
        duration_seconds: 静音时长（秒）
        sample_rate: 采样率
    
    Returns:
        静音音频数组
    """
    num_samples = int(duration_seconds * sample_rate)
    return np.zeros(num_samples, dtype=np.float32)
