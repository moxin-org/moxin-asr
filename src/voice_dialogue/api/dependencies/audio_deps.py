import base64

import numpy as np
from fastapi import HTTPException, Depends


def decode_audio_data(audio_data: str) -> np.ndarray:
    """解码Base64音频数据"""
    try:
        # 解码Base64数据
        decoded_data = base64.b64decode(audio_data)

        # 转换为numpy数组 (假设是16-bit PCM格式)
        audio_array = np.frombuffer(decoded_data, dtype=np.int16)

        # 转换为float32格式，范围[-1, 1]
        audio_array = audio_array.astype(np.float32) / 32768.0

        return audio_array
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"音频数据解码失败: {str(e)}"
        )


def encode_audio_data(audio_array: np.ndarray, sample_rate: int = 16000) -> str:
    """编码音频数据为Base64"""
    try:
        # 转换为16-bit PCM格式
        audio_int16 = (audio_array * 32767).astype(np.int16)

        # 转换为字节
        audio_bytes = audio_int16.tobytes()

        # Base64编码
        encoded_data = base64.b64encode(audio_bytes).decode('utf-8')

        return encoded_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"音频数据编码失败: {str(e)}"
        )


def validate_audio_format(audio_array: np.ndarray) -> bool:
    """验证音频格式"""
    if len(audio_array) == 0:
        raise HTTPException(
            status_code=400,
            detail="音频数据为空"
        )

    if len(audio_array) > 16000 * 30:  # 30秒限制
        raise HTTPException(
            status_code=400,
            detail="音频时长超过30秒限制"
        )

    return True
