"""设置相关的API路由"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from voice_dialogue.config.llm_config import CHINESE_SYSTEM_PROMPT, ENGLISH_SYSTEM_PROMPT
from voice_dialogue.config.user_config import (
    get_user_prompts, save_user_prompts, get_raw_prompt, reset_prompts_to_default
)

router = APIRouter()


class PromptsResponse(BaseModel):
    """获取 Prompts 的响应模型"""
    chinese_prompt: str = Field(..., description="中文系统提示词")
    english_prompt: str = Field(..., description="英文系统提示词")
    is_custom: bool = Field(..., description="是否为用户自定义")


class UpdatePromptsRequest(BaseModel):
    """更新 Prompts 的请求模型"""
    chinese_prompt: Optional[str] = Field(None, description="中文系统提示词")
    english_prompt: Optional[str] = Field(None, description="英文系统提示词")


class DefaultPromptsResponse(BaseModel):
    """默认 Prompts 的响应模型"""
    chinese_prompt: str = Field(..., description="默认中文系统提示词")
    english_prompt: str = Field(..., description="默认英文系统提示词")


@router.get("/settings/prompts", response_model=PromptsResponse, summary="获取当前生效的 Prompt")
async def get_current_prompts():
    """
    获取当前系统中正在使用的中文和英文系统 Prompt
    返回的是原始内容，不包含系统自动添加的 /no_think 指令
    """
    user_prompts = get_user_prompts()
    is_custom = bool(user_prompts)  # 如果有用户自定义配置，则认为是自定义的

    return PromptsResponse(
        chinese_prompt=get_raw_prompt("zh"),
        english_prompt=get_raw_prompt("en"),
        is_custom=is_custom
    )


@router.get("/settings/prompts/default", response_model=DefaultPromptsResponse, summary="获取默认 Prompt")
async def get_default_prompts():
    """获取系统默认的 Prompt（原始内容，不包含 /no_think）"""
    return DefaultPromptsResponse(
        chinese_prompt=CHINESE_SYSTEM_PROMPT,
        english_prompt=ENGLISH_SYSTEM_PROMPT
    )


@router.post("/settings/prompts", summary="更新并保存用户的 Prompt 设置")
async def update_user_prompts(request: UpdatePromptsRequest):
    """
    更新用户自定义的 Prompt
    只更新请求体中提供的字段，未提供的字段将保持不变
    """
    try:
        # 获取当前用户配置
        current_prompts = get_user_prompts()

        # 构建更新数据
        update_data = request.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="请求体不能为空")

        # 更新配置
        current_prompts.update(update_data)

        # 保存配置
        if not save_user_prompts(current_prompts):
            raise HTTPException(status_code=500, detail="保存配置失败")

        return {"message": "用户 Prompt 更新成功", "updated_fields": list(update_data.keys())}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新 Prompt 失败: {str(e)}")


@router.delete("/settings/prompts", summary="重置 Prompt 为默认值")
async def reset_prompts():
    """重置用户自定义的 Prompt 为系统默认值"""
    try:
        if not reset_prompts_to_default():
            raise HTTPException(status_code=500, detail="重置失败")

        return {"message": "Prompt 已重置为默认值"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置 Prompt 失败: {str(e)}")
