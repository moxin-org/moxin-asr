import time
import typing
from queue import Queue, Empty

import numpy as np

from voice_dialogue.core.base import BaseThread
from voice_dialogue.core.constants import user_still_speaking_event, voice_state_manager, dropped_audio_cache
from voice_dialogue.models.voice_task import VoiceTask
from voice_dialogue.services.mixins import PerformanceLogMixin
from voice_dialogue.utils.cache import LRUCacheDict
from voice_dialogue.asr import asr_manager


class ASRService(BaseThread, PerformanceLogMixin):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None,
                 user_voice_queue: Queue,
                 transcribed_text_queue: Queue,
                 language: typing.Literal["auto", "zh", "en"]):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self.language = language
        self.user_voice_queue = user_voice_queue
        self.transcribed_text_queue = transcribed_text_queue

        self.cached_user_questions = LRUCacheDict(maxsize=10)

    def run(self):
        self.client = asr_manager.create_asr(self.language)
        self.client.setup()
        self.client.warmup()

        self.is_ready = True

        while not self.is_exited:
            try:
                voice_task: VoiceTask = self.user_voice_queue.get(block=True, timeout=1)
            except Empty:
                continue

            voice_task.language = self.language
            voice_task.whisper_start_time = time.time()

            user_voice: np.array = voice_task.user_voice
            transcribed_text = self.client.transcribe(user_voice)
            if not transcribed_text.strip():
                voice_state_manager.reset_task_id()
                continue

            self.log_task_user_question(voice_task)

            voice_task.whisper_end_time = time.time()

            task_id = voice_task.id

            cached_user_question = self.cached_user_questions.get(task_id, [])
            if voice_task.is_over_audio_frames_threshold:
                cached_user_question.append(transcribed_text)
                self.cached_user_questions[task_id] = cached_user_question

            answer_id = voice_task.answer_id
            if user_still_speaking_event.is_set():
                voice_state_manager.drop_audio_task(task_id)
                dropped_audio_cache[answer_id] = answer_id
                user_still_speaking_event.clear()
                continue

            if answer_id in dropped_audio_cache:
                continue

            voice_task.transcribed_text = ' '.join(cached_user_question) if cached_user_question else transcribed_text

            voice_task.user_voice = []
            self.transcribed_text_queue.put(voice_task.model_copy())
