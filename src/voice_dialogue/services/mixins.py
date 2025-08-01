from collections import OrderedDict

from voice_dialogue.core.constants import (
    voice_state_manager, session_manager, dropped_audio_cache,
    user_still_speaking_event, chat_history_cache, is_debug_mode
)
from voice_dialogue.models.voice_task import VoiceTask
from voice_dialogue.utils.logger import logger


class TaskStatusMixin:
    """提供语音任务状态检查和中断处理的通用功能"""

    def is_task_interrupted(self, voice_task: VoiceTask) -> bool:
        """检查语音任务是否被其他任务中断"""
        if not voice_state_manager.interrupt_task_id:
            return False

        if voice_task.id != voice_state_manager.interrupt_task_id:
            logger.info(f"任务<{voice_task.id}> 被任务<{voice_state_manager.interrupt_task_id}> 中断")
            return True
        
        return False

    def is_task_valid(self, voice_task: VoiceTask) -> bool:
        """检查语音任务是否有效（会话匹配、未被丢弃等）"""
        if self.is_task_interrupted(voice_task):
            return False
        if voice_task.session_id != session_manager.current_id:
            logger.info(f"任务<{voice_task.id}> 会话不匹配: {voice_task.session_id} != {session_manager.current_id}")
            return False
        if voice_task.answer_id in dropped_audio_cache:
            logger.info(f"任务<{voice_task.id}> 被丢弃: {voice_task.answer_id}")
            return False
        return True

    def handle_user_speaking_interruption(self, voice_task: VoiceTask) -> bool:
        """处理用户继续说话导致的中断"""
        if user_still_speaking_event.is_set():
            logger.info(f'用户仍在说话，丢弃任务 {voice_task.id}')
            voice_state_manager.drop_audio_task(voice_task.id)
            dropped_audio_cache[voice_task.answer_id] = voice_task.answer_id
            user_still_speaking_event.clear()
            return True
        return False


class HistoryMixin:
    """提供更新聊天历史记录的功能"""

    def update_chat_history(self, voice_task: VoiceTask) -> None:
        """更新会话的聊天历史"""
        chat_history = chat_history_cache.get(voice_task.session_id, OrderedDict())
        task_answer_id = voice_task.answer_id

        user_question_key = f'{task_answer_id}:human'
        if user_question_key not in chat_history:
            chat_history[user_question_key] = voice_task.transcribed_text

        ai_answer_key = f'{task_answer_id}:ai'
        cached_ai_answer = chat_history.get(ai_answer_key, [])
        cached_ai_answer.append(voice_task.answer_sentence)
        chat_history[ai_answer_key] = cached_ai_answer

        chat_history_cache[voice_task.session_id] = chat_history


class PerformanceLogMixin:
    """提供记录任务性能日志的功能"""

    def log_task_performance(self, voice_task: VoiceTask, task_name: str = "任务"):
        """记录ASR, LLM, TTS各阶段耗时和音频长度"""
        if not is_debug_mode():
            return

        try:
            from voice_dialogue.utils.audio_utils import calculate_audio_duration

            asr_duration = getattr(voice_task, 'whisper_end_time', 0) - getattr(voice_task, 'whisper_start_time', 0)
            llm_duration = getattr(voice_task, 'llm_end_time', 0) - getattr(voice_task, 'llm_start_time', 0)
            tts_duration = getattr(voice_task, 'tts_end_time', 0) - getattr(voice_task, 'tts_start_time', 0)

            audio_duration = 0
            if hasattr(voice_task, 'tts_generated_sentence_audio') and voice_task.tts_generated_sentence_audio:
                audio_data, sample_rate = voice_task.tts_generated_sentence_audio
                audio_duration = calculate_audio_duration(audio_data, sample_rate)

            logger.info(
                f"\n"
                f"┌───────────────────────── 任务信息  ───────────────────────┐\n"
                f"│ 任务ID: {voice_task.id}\n"
                f"├───────────────────────── 性能统计 ────────────────────────┤\n"
                f"│ ASR 耗时: {asr_duration:.2f}s\n"
                f"│ LLM 耗时: {llm_duration:.2f}s\n"
                f"│ TTS 耗时: {tts_duration:.2f}s\n"
                f"│ 音频长度: {audio_duration:.2f}s\n"
                f"├───────────────────────── 生成内容 ────────────────────────┤\n"
                f"│-> {voice_task.answer_sentence}\n"
                f"└──────────────────────────────────────────────────────────┘"
            )
        except Exception as e:
            logger.error(f"记录任务性能信息时出错: {e}")

    def log_task_user_question(self, voice_task: VoiceTask):
        if not is_debug_mode():
            return

        from voice_dialogue.config.paths import PROJECT_ROOT
        output_path = PROJECT_ROOT / "output"
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        import soundfile as sf
        output_filename = output_path / (voice_task.id + ".wav")
        sf.write(output_filename.as_posix(), voice_task.user_voice, 16000, subtype="PCM_16")
