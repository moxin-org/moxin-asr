import asyncio
import time

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request

from voice_dialogue.core.constants import session_manager
from voice_dialogue.utils.logger import logger
from ..core.service_factories import get_audio_capture_service_definition, get_speech_monitor_service_definition
from ..schemas.system_schemas import (
    SystemStatusResponse, SystemResponse, SystemStartRequest
)

router = APIRouter()

# 全局系统状态
_system_status = {
    "status": "stopped",
    "start_time": None,
    "active_sessions": 0
}


@router.get("/status", response_model=SystemStatusResponse, summary="获取系统状态")
async def get_system_status(request: Request):
    """
    获取系统整体状态，包含服务运行状态
    """
    try:
        # 从应用状态获取服务管理器
        service_manager = getattr(request.app.state, "service_manager", None)
        system_running = getattr(request.app.state, "system_running", False)

        # 获取服务状态
        services_status = {}
        if service_manager:
            services_status = service_manager.get_service_status()

        # 检查audio_capture服务状态
        audio_capture_running = False
        audio_capture_ready = False
        if service_manager and service_manager.is_service_running("audio_capture"):
            audio_capture_service = service_manager.get_service("audio_capture")
            if audio_capture_service:
                audio_capture_running = True
                audio_capture_ready = audio_capture_service.is_ready

        return SystemStatusResponse(
            status=_system_status["status"],
            uptime=time.time() - _system_status["start_time"] if _system_status["start_time"] else None,
            active_sessions=_system_status["active_sessions"],
            system_running=system_running,
            services_count=services_status.get("total_services", 0),
            audio_capture_running=audio_capture_running,
            audio_capture_ready=audio_capture_ready,
            services_details=services_status
        )

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@router.post("/start", response_model=SystemResponse, summary="启动系统")
async def start_system(
        request: SystemStartRequest,
        fastapi_request: Request,
        background_tasks: BackgroundTasks
):
    """
    启动语音对话系统 - 创建audio_capture服务
    """
    try:
        if _system_status["status"] in ["running", "starting"]:
            return SystemResponse(
                success=False,
                message="系统已经在运行中或正在启动"
            )

        # 更新状态
        _system_status["status"] = "starting"
        session_manager.reset_id()

        # 在后台启动系统
        background_tasks.add_task(
            _start_system_background,
            fastapi_request,
            request.enable_echo_cancellation
        )

        return SystemResponse(
            success=True,
            message="系统启动请求已提交，正在后台启动..."
        )

    except Exception as e:
        logger.error(f"系统启动失败: {e}", exc_info=True)
        _system_status["status"] = "stopped"
        raise HTTPException(status_code=500, detail=f"系统启动失败: {str(e)}")


@router.post("/stop", response_model=SystemResponse, summary="停止系统")
async def stop_system(request: Request):
    """
    停止语音对话系统 - 停止audio_capture服务
    """
    try:
        if _system_status["status"] == "stopped":
            return SystemResponse(
                success=False,
                message="系统已经停止"
            )

        # 更新状态
        _system_status["status"] = "stopping"

        # 获取服务管理器
        service_manager = getattr(request.app.state, "service_manager", None)
        if service_manager:
            # 停止audio_capture服务
            if service_manager.is_service_running("audio_capture"):
                audio_capture_service = service_manager.get_service("audio_capture")
                if audio_capture_service:
                    try:
                        audio_capture_service.stop()
                        logger.info("音频捕获服务已停止")

                        # 等待服务停止
                        timeout = 5
                        start_time = time.time()
                        while audio_capture_service.is_alive() and (time.time() - start_time) < timeout:
                            await asyncio.sleep(0.1)

                        # 从服务管理器中移除
                        if "audio_capture" in service_manager.services:
                            del service_manager.services["audio_capture"]

                    except Exception as e:
                        logger.error(f"停止音频捕获服务时发生错误: {e}", exc_info=True)

            # 停止语音监控服务
            if service_manager.is_service_running("speech_monitor"):
                speech_monitor_service = service_manager.get_service("speech_monitor")
                if speech_monitor_service:
                    try:
                        speech_monitor_service.exit()
                        logger.info("语音监控服务已停止")

                        # 等待服务停止
                        timeout = 5
                        start_time = time.time()
                        while speech_monitor_service.is_alive() and (time.time() - start_time) < timeout:
                            await asyncio.sleep(0.1)

                        # 从服务管理器中移除
                        if "speech_monitor" in service_manager.services:
                            del service_manager.services["speech_monitor"]

                    except Exception as e:
                        logger.error(f"停止语音监控服务时发生错误: {e}", exc_info=True)


            # 停止audio_player服务
            if service_manager.is_service_running("audio_player"):
                audio_player_service = service_manager.get_service("audio_player")
                if audio_player_service:
                    try:
                        # 首先停止音频播放
                        audio_player_service.stop()
                        logger.info("音频播放服务已停止播放")
                        
                        # 等待当前播放完成，但设置超时
                        timeout = 3
                        start_time = time.time()
                        while not audio_player_service.is_stopped and (time.time() - start_time) < timeout:
                            await asyncio.sleep(0.1)
                            
                        logger.info("音频播放服务停止完成")
                        
                    except Exception as e:
                        logger.error(f"停止音频播放服务时发生错误: {e}", exc_info=True)

        _system_status["status"] = "stopped"
        _system_status["start_time"] = None
        _system_status["active_sessions"] = 0

        return SystemResponse(
            success=True,
            message="系统已成功停止"
        )

    except Exception as e:
        logger.error(f"系统停止失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系统停止失败: {str(e)}")


@router.post("/restart", response_model=SystemResponse, summary="重启系统")
async def restart_system(
        fastapi_request: Request,
        background_tasks: BackgroundTasks
):
    """
    重启语音对话系统
    """
    try:
        # 先停止
        if _system_status["status"] != "stopped":
            await stop_system(fastapi_request)

        # 再启动
        return await start_system(fastapi_request, background_tasks)

    except Exception as e:
        logger.error(f"系统重启失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系统重启失败: {str(e)}")


async def _start_system_background(request: Request, enable_echo_cancellation: bool = True):
    """
    后台启动系统的实际逻辑 - 创建并启动audio_capture服务
    """
    try:
        logger.info("开始启动语音对话系统...")

        # 获取服务管理器
        service_manager = getattr(request.app.state, "service_manager", None)
        if not service_manager:
            raise RuntimeError("服务管理器未初始化")

        audio_player_service = service_manager.get_service("audio_player")
        if audio_player_service:
            try:
                if audio_player_service.is_stopped:
                    # 如果服务处于停止状态，恢复运行
                    audio_player_service.resume()
                    logger.info("音频播放服务已恢复运行")
                elif not audio_player_service.is_ready:
                    # 如果服务未准备就绪，等待一段时间
                    timeout = 5
                    start_time = time.time()
                    while not audio_player_service.is_ready and (time.time() - start_time) < timeout:
                        await asyncio.sleep(0.1)
                    
                    if audio_player_service.is_ready:
                        logger.info("音频播放服务已准备就绪")
                    else:
                        logger.warning("音频播放服务启动超时，但继续启动系统")
                else:
                    logger.info("音频播放服务已在运行中")
                    
            except Exception as e:
                logger.error(f"处理音频播放服务时发生错误: {e}", exc_info=True)
                # 不因为audio_player错误而阻止系统启动
        else:
            logger.warning("未找到音频播放服务，系统将继续启动但可能无法播放音频")

        if service_manager.is_service_running("speech_monitor"):
            logger.info("语音监控服务已在运行")
        else:
            # 创建语音监控服务定义
            enable_vad = not enable_echo_cancellation
            speech_monitor_def = get_speech_monitor_service_definition(enable_vad)

            # 启动语音监控服务
            success = service_manager.start_service(speech_monitor_def)
            if not success:
                raise RuntimeError("语音监控服务启动失败")
            logger.info("语音监控服务启动成功")

        # 检查audio_capture服务是否已存在
        if service_manager.is_service_running("audio_capture"):
            logger.info("音频捕获服务已在运行")
        else:
            # 创建audio_capture服务定义
            audio_capture_def = get_audio_capture_service_definition(enable_echo_cancellation)

            # 启动audio_capture服务
            success = service_manager.start_service(audio_capture_def)
            if not success:
                raise RuntimeError("音频捕获服务启动失败")

            logger.info("音频捕获服务启动成功")

        _system_status["status"] = "running"
        _system_status["start_time"] = time.time()

        logger.info("语音对话系统启动成功")

    except Exception as e:
        logger.error(f"后台启动系统失败: {e}", exc_info=True)
        _system_status["status"] = "stopped"


@router.post("/pause", response_model=SystemResponse, summary="暂停系统")
async def pause_system(request: Request):
    """
    暂停语音对话系统
    """
    try:
        # 检查当前状态是否允许暂停
        if _system_status["status"] == "stopped":
            return SystemResponse(
                success=False,
                message="系统未启动，无法暂停"
            )

        if _system_status["status"] == "paused":
            return SystemResponse(
                success=False,
                message="系统已经暂停"
            )

        if _system_status["status"] in ["starting", "stopping"]:
            return SystemResponse(
                success=False,
                message="系统正在启动或停止中，请稍后再试"
            )

        # 获取服务管理器
        service_manager = getattr(request.app.state, "service_manager", None)
        if not service_manager:
            return SystemResponse(
                success=False,
                message="服务管理器未初始化"
            )

        # 获取音频捕获服务
        audio_capture_service = service_manager.get_service("audio_capture")
        if not audio_capture_service:
            return SystemResponse(
                success=False,
                message="音频捕获服务未找到"
            )

        # 检查服务是否正在运行
        if not service_manager.is_service_running("audio_capture"):
            return SystemResponse(
                success=False,
                message="音频捕获服务未运行"
            )

        # 暂停音频捕获服务
        try:
            audio_capture_service.pause()
            logger.info("音频捕获服务已暂停")
        except Exception as e:
            logger.error(f"暂停音频捕获服务失败: {e}", exc_info=True)
            return SystemResponse(
                success=False,
                message=f"暂停音频捕获服务失败: {str(e)}"
            )

        # 更新系统状态
        _system_status["status"] = "paused"

        return SystemResponse(
            success=True,
            message="语音对话系统已成功暂停"
        )

    except Exception as e:
        logger.error(f"暂停语音对话系统失败: {e}", exc_info=True)
        # 恢复状态
        if _system_status["status"] == "paused":
            _system_status["status"] = "running"
        raise HTTPException(status_code=500, detail=f"暂停语音对话系统失败: {str(e)}")


@router.post("/resume", response_model=SystemResponse, summary="恢复系统")
async def resume_system(request: Request):
    """
    恢复语音对话系统
    """
    try:
        # 检查当前状态是否允许恢复
        if _system_status["status"] == "stopped":
            return SystemResponse(
                success=False,
                message="系统未启动，请先启动系统"
            )

        if _system_status["status"] == "running":
            return SystemResponse(
                success=False,
                message="系统已经在运行中"
            )

        if _system_status["status"] in ["starting", "stopping"]:
            return SystemResponse(
                success=False,
                message="系统正在启动或停止中，请稍后再试"
            )

        if _system_status["status"] != "paused":
            return SystemResponse(
                success=False,
                message="只有暂停状态的系统才能恢复"
            )

        # 获取服务管理器
        service_manager = getattr(request.app.state, "service_manager", None)
        if not service_manager:
            return SystemResponse(
                success=False,
                message="服务管理器未初始化"
            )

        # 获取音频捕获服务
        audio_capture_service = service_manager.get_service("audio_capture")
        if not audio_capture_service:
            return SystemResponse(
                success=False,
                message="音频捕获服务未找到"
            )

        # 检查服务是否存在（可能已被停止）
        if not service_manager.is_service_running("audio_capture"):
            return SystemResponse(
                success=False,
                message="音频捕获服务未运行，请重新启动系统"
            )

        # 恢复音频捕获服务
        try:
            audio_capture_service.resume()
            logger.info("音频捕获服务已恢复运行")
        except Exception as e:
            logger.error(f"恢复音频捕获服务失败: {e}", exc_info=True)
            return SystemResponse(
                success=False,
                message=f"恢复音频捕获服务失败: {str(e)}"
            )

        # 更新系统状态为运行中
        _system_status["status"] = "running"

        return SystemResponse(
            success=True,
            message="语音对话系统已成功恢复运行"
        )

    except Exception as e:
        logger.error(f"恢复语音对话系统失败: {e}", exc_info=True)
        # 恢复状态
        if _system_status["status"] == "running":
            _system_status["status"] = "paused"
        raise HTTPException(status_code=500, detail=f"恢复语音对话系统失败: {str(e)}")
