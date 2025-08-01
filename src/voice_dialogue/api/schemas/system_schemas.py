from typing import Optional, Literal, Dict, Any

from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    status: Literal['running', 'stopped', 'paused', 'starting', 'stopping', 'resuming'] = Field(..., description="系统状态")
    uptime: Optional[float] = Field(None, description="运行时间(秒)")
    active_sessions: int = Field(default=0, description="活跃会话数")
    system_running: bool = Field(default=False, description="系统是否运行中")
    services_count: int = Field(default=0, description="运行中的服务数量")
    audio_capture_running: bool = Field(default=False, description="音频捕获服务是否运行")
    audio_capture_ready: bool = Field(default=False, description="音频捕获服务是否就绪")
    services_details: Optional[Dict[str, Any]] = Field(None, description="服务详细状态信息")


class SystemStartRequest(BaseModel):
    """系统启动请求"""
    enable_echo_cancellation: bool = Field(default=True, description="是否启用回声消除")


class SystemResponse(BaseModel):
    """系统操作响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
