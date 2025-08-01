import time
from multiprocessing import Queue
from queue import Empty

from voice_dialogue.core.base import BaseThread
from voice_dialogue.core.constants import voice_state_manager
from voice_dialogue.models.voice_task import VoiceTask
from voice_dialogue.services.mixins import TaskStatusMixin
from voice_dialogue.services.utils import has_no_words
from voice_dialogue.tts import tts_manager, BaseTTSConfig
from voice_dialogue.utils.logger import logger


class TTSAudioGenerator(BaseThread, TaskStatusMixin):
    """
    TTS 音频生成器 - 负责将文本转换为音频

    这个类是一个多线程音频生成器，主要功能包括：
    1. 从处理完的答案队列中获取语音任务
    2. 使用TTS引擎将文本转换为音频
    3. 处理用户打断和音频缓存逻辑
    4. 将生成的音频任务放入音频队列中
    """

    def __init__(
            self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None,
            text_input_queue: Queue,
            audio_output_queue: Queue,
            tts_config: BaseTTSConfig,
    ):
        """
        初始化TTS音频生成器

        Args:
            text_input_queue: 文本输入队列，包含待转换的文本任务
            audio_output_queue: 音频输出队列，用于输出转换后的音频
            tts_config: TTS配置对象，包含语音合成的相关设置
        """

        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self.text_input_queue: Queue = text_input_queue
        self.audio_output_queue: Queue = audio_output_queue

        self.tts_instance = tts_manager.create_tts(tts_config)

    def run(self):
        """
        主运行循环
        
        执行流程：
        1. 初始化和预热TTS引擎
        2. 持续监听处理队列
        3. 处理语音任务和中断逻辑
        4. 生成音频并放入输出队列
        """

        self.tts_instance.setup()
        self.tts_instance.warmup()

        self.is_ready = True

        while not self.is_exited:
            try:
                voice_task: VoiceTask = self.text_input_queue.get(block=True, timeout=1)
                if not voice_task:
                    continue

                self._process_task(voice_task)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"TTSAudioGenerator 主循环错误: {e}")
                time.sleep(0.1)

    def _process_task(self, voice_task: VoiceTask):
        """处理单个文本到语音任务"""
        if not voice_task.answer_sentence:
            return

        if self.handle_user_speaking_interruption(voice_task):
            return

        if not self.is_task_valid(voice_task):
            logger.info(f"TTS 音频生成: 任务<{voice_task.id}> 无效")
            return

        if has_no_words(voice_task.answer_sentence):
            logger.info(f"跳过仅包含标点的文本: '{voice_task.answer_sentence}'")
            return

        logger.info(f"TTS 音频生成: {voice_task.answer_sentence}")

        voice_task.tts_start_time = time.time()
        try:
            tts_generated_sentence_audio = self.tts_instance.synthesize(voice_task.answer_sentence)
        except Exception as e:
            logger.error(f"TTS 音频生成失败: {e}")
            voice_state_manager.reset_task_id()
            return

        voice_task.tts_generated_sentence_audio = tts_generated_sentence_audio
        voice_task.tts_end_time = time.time()

        self.audio_output_queue.put(voice_task.model_copy())
