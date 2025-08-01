from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from voice_dialogue.asr import asr_manager
from voice_dialogue.utils.logger import logger
from ..core.service_factories import get_asr_worker_service_definition
from ..schemas.asr_schemas import (
    SupportedLanguagesResponse, ASRInstanceRequest, ASRInstanceResponse
)

router = APIRouter()

_asr_creation_status = {
    "status": "idle",  # idle, creating, completed, failed
    "current_language": None,
    "current_asr_type": None,
    "instance_id": None,
    "message": None
}


@router.get("/languages", response_model=SupportedLanguagesResponse, summary="获取支持的识别语言")
async def get_supported_languages(fastapi_request: Request):
    """
    获取系统支持的语音识别语言列表，包括语言映射和可用引擎
    """
    try:
        available_languages = asr_manager.get_available_languages()
        language_mappings = asr_manager._language_to_asr_mapping
        asr_engines = list(asr_manager.list_registered_asr().keys())
        current_asr_language = getattr(fastapi_request.app.state, "current_asr_language", None)

        return SupportedLanguagesResponse(
            languages=available_languages,
            language_mappings=language_mappings,
            asr_engines=asr_engines,
            current_asr_language=current_asr_language
        )
    except Exception as e:
        logger.error(f"获取支持语言列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取支持语言列表失败: {str(e)}")


@router.post("/instance/create", response_model=ASRInstanceResponse, summary="创建ASR实例")
async def create_asr_instance(
        request: ASRInstanceRequest,
        fastapi_request: Request,
        background_tasks: BackgroundTasks
):
    """
    根据指定语言创建新的ASR实例
    """
    try:
        # 检查是否正在创建实例
        if _asr_creation_status["status"] == "creating":
            return ASRInstanceResponse(
                success=False,
                message="ASR实例正在创建中，请稍后重试",
                language=request.language,
                asr_type=None,
                instance_id=None
            )

        # 检查当前语言是否已存在且相同
        current_asr_language = getattr(fastapi_request.app.state, "current_asr_language", None)
        if current_asr_language and current_asr_language == request.language:
            asr_type = asr_manager._get_asr_type_for_language(request.language)
            return ASRInstanceResponse(
                success=True,
                message=f"ASR实例已存在，语言: {request.language}",
                language=request.language,
                asr_type=asr_type,
                instance_id=f"{asr_type}_{request.language}"
            )

        # 更新状态为创建中
        _asr_creation_status["status"] = "creating"
        _asr_creation_status["current_language"] = request.language
        _asr_creation_status["message"] = "正在创建ASR实例..."

        # 在后台执行创建任务
        background_tasks.add_task(
            _create_asr_instance_background,
            request,
            fastapi_request
        )

        # 获取预计使用的ASR类型
        asr_type = asr_manager._get_asr_type_for_language(request.language)

        return ASRInstanceResponse(
            success=True,
            message="ASR实例创建请求已提交，正在后台创建...",
            language=request.language,
            asr_type=asr_type,
            instance_id=f"{asr_type}_{request.language}"
        )

    except ValueError as e:
        logger.warning(f"创建ASR实例失败 - 参数错误: {e}")
        _asr_creation_status["status"] = "failed"
        _asr_creation_status["message"] = str(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建ASR实例失败: {e}", exc_info=True)
        _asr_creation_status["status"] = "failed"
        _asr_creation_status["message"] = str(e)
        raise HTTPException(status_code=500, detail=f"创建ASR实例失败: {str(e)}")


async def _create_asr_instance_background(request: ASRInstanceRequest, fastapi_request: Request):
    """
    后台创建ASR实例的实际逻辑
    """
    try:
        logger.info(f"开始创建ASR实例，语言: {request.language}")

        # 获取最优的ASR引擎
        asr_type = asr_manager._get_asr_type_for_language(request.language)
        _asr_creation_status["current_asr_type"] = asr_type

        # 获取服务管理器
        service_manager = getattr(fastapi_request.app.state, "service_manager", None)
        if not service_manager:
            raise RuntimeError("服务管理器未初始化")

        # 检查是否需要重新创建服务
        current_asr_language = getattr(fastapi_request.app.state, "current_asr_language", None)
        if current_asr_language and current_asr_language != request.language:
            logger.info(f"请求语言({request.language})与当前语言({current_asr_language})不同，需要重新创建服务")

            # 停止现有的ASR服务
            if service_manager.is_service_running("asr_worker"):
                service_manager._stop_single_service("asr_worker")
                logger.info("已停止现有ASR服务")

        # 启动新的ASR服务
        asr_worker_def = get_asr_worker_service_definition(request.language)
        success = service_manager.start_service(asr_worker_def)
        if not success:
            raise RuntimeError("ASR服务启动失败")

        # 更新请求状态中的当前语言
        fastapi_request.app.state.current_asr_language = request.language

        # 生成实例ID
        instance_id = f"{asr_type}_{request.language}"
        _asr_creation_status["instance_id"] = instance_id

        # 更新状态为完成
        _asr_creation_status["status"] = "completed"
        _asr_creation_status["message"] = f"成功创建ASR实例: {instance_id}"

        logger.info(f"ASR实例创建成功: {instance_id}")

    except Exception as e:
        logger.error(f"后台创建ASR实例失败: {e}", exc_info=True)
        _asr_creation_status["status"] = "failed"
        _asr_creation_status["message"] = str(e)
