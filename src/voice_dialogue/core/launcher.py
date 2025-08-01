"""
语音对话系统启动器

负责启动和协调语音对话系统的所有组件
"""

import time

from voice_dialogue.audio.capture import AudioCapture
from voice_dialogue.config.speaker_config import get_tts_config_by_speaker_name, get_available_speaker_names
from voice_dialogue.core.constants import (
    audio_frames_queue,
    user_voice_queue,
    transcribed_text_queue,
    text_input_queue,
    audio_output_queue
)
from voice_dialogue.services import ASRService, LLMService, AudioPlayerService, SpeechStateMonitor, TTSAudioGenerator
from voice_dialogue.utils.logger import logger


def launch_system(
        user_language: str,
        speaker: str,
        disable_echo_cancellation: bool = False,
) -> None:
    """
    启动完整的语音对话系统

    该函数负责启动并协调语音对话系统的所有组件，包括音频采集、语音识别、
    文本生成、语音合成和音频播放等功能模块。系统采用多线程架构，各组件
    通过队列进行数据传递和通信。

    系统工作流程：
    1. 音频采集：EchoCancellingAudioCapture 采集用户语音并进行回声消除
    2. 语音监测：SpeechStateMonitor 检测用户是否在说话
    3. 语音识别：ASRWorker 将用户语音转换为文本
    4. 文本生成：LLMResponseGenerator 基于用户问题生成AI回答
    5. 语音合成：TTSAudioGenerator 将AI回答转换为语音
    6. 音频播放：AudioStreamPlayer 播放生成的语音

    Args:
        user_language (str): 用户语言，支持 'zh'（中文）和 'en'（英文）
        speaker (str): 语音合成使用的说话人，支持：
                      '罗翔', '马保国', '沈逸', '杨幂', '周杰伦', '马云'

    Raises:
        ValueError: 当指定的说话人不在支持列表中时抛出异常

    Returns:
        None: 函数会一直运行直到所有线程结束

    Note:
        该函数会阻塞运行，直到系统被外部停止或发生异常
    """
    # 导入speaker配置相关功能

    threads = []

    # 语音识别
    asr_worker = ASRService(
        user_voice_queue=user_voice_queue,
        transcribed_text_queue=transcribed_text_queue,
        language=user_language
    )
    asr_worker.daemon = True
    asr_worker.start()
    threads.append(asr_worker)

    # 文本生成
    text_generator = LLMService(
        user_question_queue=transcribed_text_queue,
        generated_answer_queue=text_input_queue
    )
    text_generator.daemon = True
    text_generator.start()
    threads.append(text_generator)

    # 动态获取TTS配置
    tts_speaker_config = get_tts_config_by_speaker_name(speaker)
    if tts_speaker_config is None:
        # 如果找不到指定说话人，列出所有可用说话人并抛出异常
        available_speakers = get_available_speaker_names()
        raise ValueError(f"不支持的TTS说话人: {speaker}。可用说话人: {', '.join(available_speakers)}")

    # 语音合成
    audio_generator = TTSAudioGenerator(
        text_input_queue=text_input_queue,
        audio_output_queue=audio_output_queue,
        tts_config=tts_speaker_config
    )
    audio_generator.daemon = True
    audio_generator.start()
    threads.append(audio_generator)

    # 音频播放
    audio_player = AudioPlayerService(audio_playing_queue=audio_output_queue)
    audio_player.daemon = True
    audio_player.start()
    threads.append(audio_player)

    # 语音状态监测
    enable_vad = disable_echo_cancellation
    speech_monitor = SpeechStateMonitor(
        audio_frame_queue=audio_frames_queue,
        user_voice_queue=user_voice_queue,
        enable_vad=enable_vad
    )
    speech_monitor.daemon = True
    speech_monitor.start()
    threads.append(speech_monitor)

    # 音频采集
    enable_echo_cancellation = not disable_echo_cancellation
    audio_capture = AudioCapture(
        audio_frames_queue=audio_frames_queue,
        enable_echo_cancellation=enable_echo_cancellation
    )
    audio_capture.daemon = True
    audio_capture.start()
    threads.append(audio_capture)

    # 等待所有线程准备就绪
    while not all([thread.is_ready for thread in threads]):
        time.sleep(0.1)

    logger.info(
        f'\n'
        f"┌──────────────────────────────────────────┐\n"
        f"│                                          │\n"
        f"│             🚀 服务启动成功 🚀             │\n"
        f"│                                          │\n"
        f"└──────────────────────────────────────────┘"
    )

    # 等待所有线程结束
    for thread in threads:
        thread.join()
