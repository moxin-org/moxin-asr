import hashlib
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class TTSModelInfo(BaseModel):
    """TTS模型基础信息"""
    id: str = Field(..., description="模型唯一标识符")
    character_name: str = Field(..., description="角色名称")
    cover_image: str = Field(..., description="封面图片URL")
    description: str = Field(..., description="模型描述")
    file_size: str = Field(..., description="文件大小")
    is_chinese_voice: bool = Field(..., description="是否为中文语音")
    status: Literal['not_downloaded', 'downloading', 'downloaded', 'failed'] = Field(..., description="模型状态")


class TTSModelListResponse(BaseModel):
    """TTS模型列表响应"""
    total: int = Field(..., description="模型总数")
    models: List[TTSModelInfo] = Field(..., description="TTS模型列表")
    current_model_id: Optional[str] = Field(None, description="当前使用的模型ID")
    current_character_name: Optional[str] = Field(None, description="当前使用的角色名称")


class TTSModelLoadRequest(BaseModel):
    """TTS模型加载请求"""
    model_id: str = Field(..., description="要加载的模型ID")


class TTSModelLoadResponse(BaseModel):
    """TTS模型加载响应"""
    success: bool = Field(..., description="是否加载成功")
    message: str = Field(..., description="响应消息")
    model_id: str = Field(..., description="模型ID")


class TTSModelStatusResponse(BaseModel):
    """TTS模型状态响应"""
    model_id: str = Field(..., description="模型ID")
    status: Literal['not_downloaded', 'downloading', 'downloaded', 'failed'] = Field(..., description="模型状态")
    progress: Optional[float] = Field(None, description="下载进度(0-100)")


class TTSModelDeleteResponse(BaseModel):
    """TTS模型删除响应"""
    success: bool = Field(..., description="是否删除成功")
    message: str = Field(..., description="响应消息")
    model_id: str = Field(..., description="模型ID")


def generate_model_id(tts_type: str, character_name: str) -> str:
    """生成模型唯一ID"""
    combined = f"{tts_type}:{character_name}"
    return hashlib.md5(combined.encode()).hexdigest()[:16] 