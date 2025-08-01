from voice_dialogue.audio.capture import AudioCapture
from voice_dialogue.core.constants import (
    transcribed_text_queue, text_input_queue, audio_output_queue,
    audio_frames_queue, user_voice_queue, websocket_message_queue
)
from voice_dialogue.services import SpeechStateMonitor, ASRService, AudioPlayerService, LLMService, TTSAudioGenerator
from voice_dialogue.tts import BaseTTSConfig, tts_config_registry
from .service_manager import ServiceDefinition


class ServiceFactories:
    """服务工厂类，封装所有服务的创建逻辑"""

    @staticmethod
    def create_audio_capture(enable_echo_cancellation: bool = True) -> AudioCapture:
        """创建音频捕获服务"""
        return AudioCapture(
            audio_frames_queue=audio_frames_queue,
            enable_echo_cancellation=enable_echo_cancellation
        )

    @staticmethod
    def create_speech_monitor(enable_vad: bool = False) -> SpeechStateMonitor:
        """创建语音监控服务"""
        return SpeechStateMonitor(
            audio_frame_queue=audio_frames_queue,
            user_voice_queue=user_voice_queue,
            enable_vad=enable_vad
        )

    @staticmethod
    def create_asr_worker(language: str) -> ASRService:
        """创建ASR服务"""
        return ASRService(
            user_voice_queue=user_voice_queue,
            transcribed_text_queue=transcribed_text_queue,
            language=language
        )

    @staticmethod
    def create_llm_generator() -> LLMService:
        """创建LLM文本生成服务"""
        return LLMService(
            user_question_queue=transcribed_text_queue,
            generated_answer_queue=text_input_queue,
            websocket_message_queue=websocket_message_queue,
        )

    @staticmethod
    def create_tts_audio_generator(tts_config: BaseTTSConfig = None) -> TTSAudioGenerator:
        """创建TTS音频生成服务"""
        if tts_config is None:
            tts_config = tts_config_registry.get_default_config_for_system()

        return TTSAudioGenerator(
            text_input_queue=text_input_queue,
            audio_output_queue=audio_output_queue,
            tts_config=tts_config
        )

    @staticmethod
    def create_audio_player() -> AudioPlayerService:
        """创建音频播放服务"""
        return AudioPlayerService(
            audio_playing_queue=audio_output_queue,
            websocket_message_queue=websocket_message_queue
        )


def get_core_voice_service_definitions(system_language: str, tts_config: BaseTTSConfig = None) -> list:
    """
    获取核心语音对话服务定义配置
    
    这些服务构成完整的语音对话处理流水线：
    1. 音频捕获 -> 2. 语音监控 -> 3. 语音识别 -> 4. 文本生成 -> 5. 语音合成 -> 6. 音频播放
    
    Args:
        system_language: 系统默认语言
        tts_config: TTS配置，如果为None则使用默认配置
    
    Returns:
        list: 服务定义列表
    """
    return [
        # # 音频捕获服务（最底层服务）
        # ServiceDefinition(
        #     name="audio_capture",
        #     factory=ServiceFactories.create_audio_capture,
        #     dependencies=[],
        #     health_check=lambda service: hasattr(service, 'is_ready') and service.is_ready
        # ),

        # 语音状态监控服务
        # ServiceDefinition(
        #     name="speech_monitor",
        #     factory=ServiceFactories.create_speech_monitor,
        #     dependencies=[],
        #     health_check=lambda service: hasattr(service, 'is_ready') and service.is_ready
        # ),

        # ASR语音识别服务
        ServiceDefinition(
            name="asr_worker",
            factory=lambda: ServiceFactories.create_asr_worker(system_language),
            dependencies=[]
        ),

        # LLM文本生成服务
        ServiceDefinition(
            name="llm_generator",
            factory=ServiceFactories.create_llm_generator,
            dependencies=["asr_worker"],
            startup_timeout=180  # LLM服务启动较慢，增加超时时间
        ),

        # TTS音频生成服务
        ServiceDefinition(
            name="tts_audio_generator",
            factory=lambda: ServiceFactories.create_tts_audio_generator(tts_config),
            dependencies=["llm_generator"],
            startup_timeout=120  # TTS模型加载较慢
        ),

        # 音频播放服务（最终输出服务）
        ServiceDefinition(
            name="audio_player",
            factory=ServiceFactories.create_audio_player,
            dependencies=["tts_audio_generator"]
        )
    ]


def get_audio_capture_service_definition(enable_echo_cancellation: bool = True) -> ServiceDefinition:
    """获取音频捕获服务定义"""
    return ServiceDefinition(
        name="audio_capture",
        factory=lambda: ServiceFactories.create_audio_capture(enable_echo_cancellation),
        dependencies=[],
        health_check=lambda service: hasattr(service, 'is_ready') and service.is_ready
    )


def get_speech_monitor_service_definition(enable_vad: bool = False) -> ServiceDefinition:
    """获取语音监控服务定义"""
    return ServiceDefinition(
        name="speech_monitor",
        factory=lambda: ServiceFactories.create_speech_monitor(enable_vad),
        dependencies=[],
        health_check=lambda service: hasattr(service, 'is_ready') and service.is_ready
    )


def get_asr_worker_service_definition(language: str) -> ServiceDefinition:
    """获取ASR服务定义"""
    return ServiceDefinition(
        name="asr_worker",
        factory=lambda: ServiceFactories.create_asr_worker(language),
        dependencies=[]
    )


def get_tts_audio_generator_service_definition(tts_config: BaseTTSConfig = None) -> ServiceDefinition:
    """获取TTS音频生成服务定义"""
    return ServiceDefinition(
        name="tts_audio_generator",
        factory=lambda: ServiceFactories.create_tts_audio_generator(tts_config),
        dependencies=["llm_generator"],
        startup_timeout=45
    )


def get_service_health_checkers() -> dict:
    """获取服务健康检查器映射"""
    return {
        "audio_capture": lambda service: hasattr(service, 'is_ready') and service.is_ready,
        "speech_monitor": lambda service: hasattr(service, 'is_ready') and service.is_ready,
        "asr_worker": lambda service: hasattr(service, 'is_ready') and service.is_ready,
        "llm_generator": lambda service: hasattr(service, 'is_ready') and service.is_ready,
        "tts_audio_generator": lambda service: hasattr(service, 'is_ready') and service.is_ready,
        "audio_player": lambda service: hasattr(service, 'is_ready') and service.is_ready,
    }
