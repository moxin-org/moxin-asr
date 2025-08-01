from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse

from voice_dialogue.tts import tts_config_registry
from voice_dialogue.utils.logger import logger
from ..core.service_factories import get_tts_audio_generator_service_definition
from ..schemas.tts_schemas import (
    TTSModelInfo, TTSModelListResponse, TTSModelLoadRequest,
    TTSModelLoadResponse, TTSModelStatusResponse, generate_model_id
)

router = APIRouter()

# TTS模型加载状态管理
_tts_loading_status = {
    "status": "idle",  # idle, loading, completed, failed
    "current_model_id": None,
    "current_character_name": None,
    "message": None,
    "progress": 0.0
}


@router.get("/models", response_model=TTSModelListResponse, summary="获取TTS模型列表")
async def list_tts_models(fastapi_request: Request):
    """
    获取所有可用的TTS模型列表
    """
    try:
        all_configs = tts_config_registry.get_all_configs()
        models = []

        # 获取当前系统默认加载的TTS模型信息
        current_tts_model_id = getattr(fastapi_request.app.state, "current_tts_model_id", None)
        current_tts_character_name = getattr(fastapi_request.app.state, "current_tts_character_name", None)

        # 如果没有从请求状态获取到当前模型，尝试从系统默认配置获取
        if not current_tts_model_id:
            default_config = tts_config_registry.get_default_config_for_system()
            if default_config:
                current_tts_model_id = generate_model_id(default_config.tts_type.value, default_config.character_name)
                current_tts_character_name = default_config.character_name
                logger.info(f"使用系统默认TTS模型: {current_tts_character_name} (ID: {current_tts_model_id})")

        for config in all_configs:
            # 生成唯一ID，但不暴露具体的TTS类型
            model_id = generate_model_id(config.tts_type.value, config.character_name)

            # 检查模型状态
            if config.is_model_complete():
                # 如果是当前系统加载的模型，或者是正在加载的模型，优先显示正确状态
                if current_tts_model_id == model_id:
                    status = "downloaded"  # 系统已加载的模型
                elif (_tts_loading_status["status"] == "loading" and
                      _tts_loading_status["current_model_id"] == model_id):
                    status = "downloading"
                elif (_tts_loading_status["status"] == "failed" and
                      _tts_loading_status["current_model_id"] == model_id):
                    status = "failed"
                else:
                    status = "downloaded"
            else:
                # 模型未完整下载
                if (_tts_loading_status["status"] == "loading" and
                        _tts_loading_status["current_model_id"] == model_id):
                    status = "downloading"
                elif (_tts_loading_status["status"] == "failed" and
                      _tts_loading_status["current_model_id"] == model_id):
                    status = "failed"
                else:
                    status = "not_downloaded"

            model_info = TTSModelInfo(
                id=model_id,
                character_name=config.character_name,
                cover_image=config.cover_image,
                description=config.description,
                file_size=config.file_size,
                is_chinese_voice=config.is_chinese_voice,
                status=status
            )
            models.append(model_info)

        return TTSModelListResponse(
            total=len(models),
            models=models,
            current_model_id=current_tts_model_id,
            current_character_name=current_tts_character_name
        )

    except Exception as e:
        logger.error(f"获取TTS模型列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取TTS模型列表失败: {str(e)}")


@router.post("/models/load", response_model=TTSModelLoadResponse, summary="加载TTS模型")
async def load_tts_model(
        request: TTSModelLoadRequest,
        fastapi_request: Request,
        background_tasks: BackgroundTasks,
):
    """
    通过模型ID加载TTS模型
    """
    try:
        if _tts_loading_status["status"] == "loading":
            current_loading_model = _tts_loading_status["current_model_id"]
            if current_loading_model == request.model_id:
                return TTSModelLoadResponse(
                    success=True,
                    message=f"模型 {_tts_loading_status['current_character_name']} 正在加载中...",
                    model_id=request.model_id
                )
            else:
                return TTSModelLoadResponse(
                    success=False,
                    message="另一个模型正在加载中，请稍后重试",
                    model_id=request.model_id
                )

        # 通过ID找到对应的配置
        config = _find_config_by_id(request.model_id)
        if not config:
            raise HTTPException(status_code=404, detail="模型ID不存在")

        # 检查模型是否已经完整下载
        if config.is_model_complete():
            # 检查是否是当前系统已加载的模型
            current_tts_model_id = getattr(fastapi_request.app.state, "current_tts_model_id", None)
            if current_tts_model_id == request.model_id:
                return TTSModelLoadResponse(
                    success=True,
                    message=f"模型 {config.character_name} 已是当前系统默认模型",
                    model_id=request.model_id
                )
            else:
                # 需要切换到新的模型
                return await _switch_tts_model(request, config, fastapi_request, background_tasks)
        else:
            # 模型未下载，需要先下载再加载
            return await _download_and_load_tts_model(request, config, fastapi_request, background_tasks)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"加载TTS模型失败 - 参数错误: {e}")
        _tts_loading_status["status"] = "failed"
        _tts_loading_status["message"] = str(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"加载TTS模型失败: {e}", exc_info=True)
        _tts_loading_status["status"] = "failed"
        _tts_loading_status["message"] = str(e)
        return TTSModelLoadResponse(
            success=False,
            message=f"加载模型失败: {str(e)}",
            model_id=request.model_id
        )


async def _switch_tts_model(
        request: TTSModelLoadRequest,
        config,
        fastapi_request: Request,
        background_tasks: BackgroundTasks
) -> TTSModelLoadResponse:
    """切换到已下载的TTS模型"""
    # 更新状态为加载中
    _tts_loading_status["status"] = "loading"
    _tts_loading_status["current_model_id"] = request.model_id
    _tts_loading_status["current_character_name"] = config.character_name
    _tts_loading_status["message"] = "正在切换TTS模型..."
    _tts_loading_status["progress"] = 0.0

    # 在后台执行模型切换任务
    background_tasks.add_task(
        _switch_tts_model_background,
        config,
        request.model_id,
        fastapi_request
    )

    return TTSModelLoadResponse(
        success=True,
        message=f"模型 {config.character_name} 切换请求已提交，正在后台切换...",
        model_id=request.model_id
    )


async def _download_and_load_tts_model(
        request: TTSModelLoadRequest,
        config,
        fastapi_request: Request,
        background_tasks: BackgroundTasks
) -> TTSModelLoadResponse:
    """下载并加载TTS模型"""
    # 更新状态为加载中
    _tts_loading_status["status"] = "loading"
    _tts_loading_status["current_model_id"] = request.model_id
    _tts_loading_status["current_character_name"] = config.character_name
    _tts_loading_status["message"] = "正在下载TTS模型..."
    _tts_loading_status["progress"] = 0.0

    # 在后台执行下载和加载任务
    background_tasks.add_task(
        _download_and_load_tts_model_background,
        config,
        request.model_id,
        fastapi_request
    )

    return TTSModelLoadResponse(
        success=True,
        message=f"模型 {config.character_name} 下载和加载请求已提交，正在后台处理...",
        model_id=request.model_id
    )


async def _switch_tts_model_background(config, model_id: str, fastapi_request: Request):
    """
    后台切换TTS模型的实际逻辑
    """
    try:
        logger.info(f"开始切换TTS模型: {config.character_name}")

        # 获取服务管理器
        service_manager = getattr(fastapi_request.app.state, "service_manager", None)
        if not service_manager:
            raise RuntimeError("服务管理器未初始化")

        _tts_loading_status["progress"] = 20.0
        _tts_loading_status["message"] = "正在停止当前TTS服务..."

        # 停止当前的TTS服务
        if service_manager.is_service_running("tts_audio_generator"):
            service_manager._stop_single_service("tts_audio_generator")
            logger.info("已停止当前TTS服务")

        _tts_loading_status["progress"] = 50.0
        _tts_loading_status["message"] = "正在启动新的TTS服务..."

        # 使用新配置创建TTS服务定义
        new_tts_service_def = get_tts_audio_generator_service_definition(config)

        # 启动新的TTS服务
        success = service_manager.start_service(new_tts_service_def)
        if not success:
            raise RuntimeError("新TTS服务启动失败")

        _tts_loading_status["progress"] = 90.0
        _tts_loading_status["message"] = "正在验证服务状态..."

        # 更新请求状态中的当前模型信息
        fastapi_request.app.state.current_tts_model_id = model_id
        fastapi_request.app.state.current_tts_character_name = config.character_name

        # 更新状态为完成
        _tts_loading_status["status"] = "completed"
        _tts_loading_status["progress"] = 100.0
        _tts_loading_status["message"] = f"成功切换到TTS模型: {config.character_name}"

        logger.info(f"TTS模型切换成功: {config.character_name}")

    except Exception as e:
        logger.error(f"后台切换TTS模型失败: {e}", exc_info=True)
        _tts_loading_status["status"] = "failed"
        _tts_loading_status["message"] = str(e)
        _tts_loading_status["progress"] = 0.0


async def _download_and_load_tts_model_background(config, model_id: str, fastapi_request: Request):
    """
    后台下载并加载TTS模型的实际逻辑
    """
    try:
        logger.info(f"开始下载并加载TTS模型: {config.character_name}")

        _tts_loading_status["progress"] = 10.0
        _tts_loading_status["message"] = "正在准备下载..."

        # 执行实际的模型下载
        _tts_loading_status["progress"] = 30.0
        _tts_loading_status["message"] = "正在下载模型文件..."

        config.download_model()

        _tts_loading_status["progress"] = 70.0
        _tts_loading_status["message"] = "正在验证模型文件..."

        # 验证模型是否下载成功
        if not config.is_model_complete():
            raise RuntimeError("模型文件下载不完整")

        # 获取服务管理器
        service_manager = getattr(fastapi_request.app.state, "service_manager", None)
        if not service_manager:
            raise RuntimeError("服务管理器未初始化")

        _tts_loading_status["progress"] = 80.0
        _tts_loading_status["message"] = "正在停止当前TTS服务..."

        # 停止当前的TTS服务
        if service_manager.is_service_running("tts_audio_generator"):
            service_manager._stop_single_service("tts_audio_generator")
            logger.info("已停止当前TTS服务")

        _tts_loading_status["progress"] = 90.0
        _tts_loading_status["message"] = "正在启动新的TTS服务..."

        # 使用新配置创建TTS服务定义
        new_tts_service_def = get_tts_audio_generator_service_definition(config)

        # 启动新的TTS服务
        success = service_manager.start_service(new_tts_service_def)
        if not success:
            raise RuntimeError("新TTS服务启动失败")

        # 更新请求状态中的当前模型信息
        fastapi_request.app.state.current_tts_model_id = model_id
        fastapi_request.app.state.current_tts_character_name = config.character_name

        # 更新状态为完成
        _tts_loading_status["status"] = "completed"
        _tts_loading_status["progress"] = 100.0
        _tts_loading_status["message"] = f"成功下载并加载TTS模型: {config.character_name}"

        logger.info(f"TTS模型下载并加载成功: {config.character_name}")

    except Exception as e:
        logger.error(f"后台下载并加载TTS模型失败: {e}", exc_info=True)
        _tts_loading_status["status"] = "failed"
        _tts_loading_status["message"] = str(e)
        _tts_loading_status["progress"] = 0.0


@router.get("/models/{model_id}/status", response_model=TTSModelStatusResponse, summary="获取TTS模型状态")
async def get_tts_model_status(model_id: str, fastapi_request: Request):
    """
    获取指定TTS模型的状态
    """
    try:
        config = _find_config_by_id(model_id)
        if not config:
            raise HTTPException(status_code=404, detail="模型ID不存在")

        # 获取当前系统加载的模型
        current_tts_model_id = getattr(fastapi_request.app.state, "current_tts_model_id", None)

        # 检查模型状态
        if config.is_model_complete():
            if current_tts_model_id == model_id:
                status = "downloaded"  # 当前系统加载的模型
                progress = 100.0
            elif (_tts_loading_status["status"] == "loading" and
                  _tts_loading_status["current_model_id"] == model_id):
                status = "downloading"
                progress = _tts_loading_status["progress"]
            elif (_tts_loading_status["status"] == "failed" and
                  _tts_loading_status["current_model_id"] == model_id):
                status = "failed"
                progress = 0.0
            else:
                status = "downloaded"
                progress = 100.0
        else:
            if (_tts_loading_status["status"] == "loading" and
                    _tts_loading_status["current_model_id"] == model_id):
                status = "downloading"
                progress = _tts_loading_status["progress"]
            elif (_tts_loading_status["status"] == "failed" and
                  _tts_loading_status["current_model_id"] == model_id):
                status = "failed"
                progress = 0.0
            else:
                status = "not_downloaded"
                progress = 0.0

        return TTSModelStatusResponse(
            model_id=model_id,
            status=status,
            progress=progress
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取TTS模型状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模型状态失败: {str(e)}")


def _find_config_by_id(model_id: str) -> Optional:
    """通过模型ID找到对应的配置"""
    all_configs = tts_config_registry.get_all_configs()
    for config in all_configs:
        config_id = generate_model_id(config.tts_type.value, config.character_name)
        if config_id == model_id:
            return config
    return None


@router.get("/models/{model_id}/reference-audio", summary="获取TTS模型参考音频")
async def get_tts_model_reference_audio(model_id: str):
    """
    通过模型ID获取TTS模型的参考音频文件
    """
    try:
        # 通过ID找到对应的配置
        config = _find_config_by_id(model_id)
        if not config:
            raise HTTPException(status_code=404, detail="模型ID不存在")

        # 检查模型是否已经下载
        if not config.is_model_complete():
            raise HTTPException(status_code=400, detail="模型尚未下载，无法获取参考音频")

        # 获取参考音频文件路径
        reference_audio_path = ''
        if hasattr(config, "reference_audio_path"):
            reference_audio_path = config.reference_audio_path

        # 检查文件是否存在
        if reference_audio_path and not reference_audio_path.exists():
            raise HTTPException(status_code=404, detail="参考音频文件不存在")

        # 返回音频文件
        return FileResponse(
            path=str(reference_audio_path),
            media_type="audio/wav",
            filename=f"{config.character_name}_reference.wav"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取TTS模型参考音频失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取参考音频失败: {str(e)}")
