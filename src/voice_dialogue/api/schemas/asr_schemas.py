from typing import Literal, List, Dict, Optional

from pydantic import BaseModel, Field


class SupportedLanguagesResponse(BaseModel):
    """支持的语言响应模式"""
    languages: List[str] = Field(..., description="支持的语言列表")
    current_asr_language: str = Field(..., description="当前使用的ASR语言")
    language_mappings: Dict[str, str] = Field(..., description="语言到ASR引擎的映射")
    asr_engines: List[str] = Field(..., description="可用的ASR引擎列表")


class ASRInstanceRequest(BaseModel):
    """ASR实例请求模式"""
    language: Literal["zh", "en", "auto"] = Field(..., description="目标语言")


class ASRInstanceResponse(BaseModel):
    """ASR实例响应模式"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    language: str = Field(..., description="语言类型")
    asr_type: str = Field(..., description="使用的ASR引擎类型")
    instance_id: Optional[str] = Field(None, description="实例标识符")
