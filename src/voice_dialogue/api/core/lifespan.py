import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from voice_dialogue.tts import tts_config_registry
from voice_dialogue.utils import get_system_language, logger
from .config import TTSConfigInitializer
from .service_factories import get_core_voice_service_definitions
from .service_manager import ServiceManager
from ..schemas.tts_schemas import generate_model_id


class LifespanManager:
    """应用生命周期管理器"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.service_manager = ServiceManager()

    async def startup(self):
        """应用启动逻辑"""
        logger.info("正在启动VoiceDialogue API服务...")
        startup_start_time = time.time()

        try:
            # 初始化系统语言
            system_language = get_system_language()
            logger.info(f"系统默认语言: {system_language}")

            # 初始化TTS配置
            tts_config = TTSConfigInitializer.initialize()
            self._update_app_state(tts_config)

            default_tts_config = tts_config_registry.get_default_config_for_system()
            current_tts_model_id = None
            current_tts_character_name = None

            if default_tts_config:
                current_tts_model_id = generate_model_id(
                    default_tts_config.tts_type.value,
                    default_tts_config.character_name
                )
                current_tts_character_name = default_tts_config.character_name
                logger.info(f"系统默认TTS模型: {current_tts_character_name} (ID: {current_tts_model_id})")

            # 获取服务定义
            service_definitions = get_core_voice_service_definitions(system_language)

            # 启动所有服务
            await self._start_all_services(service_definitions)

            # 更新应用状态
            self._update_app_state({
                "service_manager": self.service_manager,
                "system_running": True,
                "system_language": system_language,
                "current_asr_language": system_language,
                "current_tts_model_id": current_tts_model_id,
                "current_tts_character_name": current_tts_character_name,
            })

            # 记录启动信息
            startup_duration = time.time() - startup_start_time
            service_status = self.service_manager.get_service_status()

            logger.info(f"VoiceDialogue API服务启动完成")
            logger.info(f"启动总耗时: {startup_duration:.2f}秒")
            logger.info(f"启动的服务数量: {service_status['total_services']}")

            if service_status['startup_errors']:
                logger.warning(f"启动时发生 {service_status['startup_errors']} 个错误")

        except Exception as e:
            logger.error(f"服务启动失败: {e}", exc_info=True)
            await self.shutdown()
            raise

    def _update_app_state(self, state_updates: dict):
        """更新应用状态"""
        for key, value in state_updates.items():
            setattr(self.app.state, key, value)

    async def _start_all_services(self, service_definitions):
        """启动所有服务"""
        for service_def in service_definitions:
            success = self.service_manager.start_service(service_def)
            if not success and service_def.required:
                raise RuntimeError(f"必需服务 {service_def.name} 启动失败")

    async def shutdown(self):
        """应用关闭逻辑"""
        logger.info("正在关闭VoiceDialogue API服务...")

        # 更新状态
        setattr(self.app.state, "system_running", False)

        # 停止所有服务
        self.service_manager.stop_all_services()

        logger.info("VoiceDialogue API服务已关闭")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI生命周期管理"""
    # 创建生命周期管理器
    lifespan_manager = LifespanManager(app)

    try:
        # 启动
        await lifespan_manager.startup()
        yield
    finally:
        # 关闭
        await lifespan_manager.shutdown()
