import uuid

from voice_dialogue.utils.cache import LRUCacheDict
from .enums import AudioState


class VoiceStateManager:
    """语音状态管理器"""

    def __init__(self):
        self._task_id = ''
        self._audio_task_states = LRUCacheDict(maxsize=10)
        self.waiting_second_answer_mapping = LRUCacheDict(maxsize=10)
        self._interrupt_task_id = ''

    @property
    def task_id(self):
        return self._task_id

    @task_id.setter
    def task_id(self, value):
        self._task_id = value

    def create_task_id(self):
        """创建新的任务ID"""
        self._task_id = f'{uuid.uuid4()}'

    def reset_task_id(self):
        """重置任务ID"""
        self._task_id = ''

    def get_audio_task_state(self, task_id):
        """获取音频任务状态"""
        return self._audio_task_states.get(task_id)

    def set_audio_playing(self, task_id):
        """设置音频为播放状态"""
        self._audio_task_states[task_id] = AudioState.PLAYING

    def drop_audio_task(self, task_id):
        """丢弃音频任务"""
        self._audio_task_states[task_id] = AudioState.DROP

    def cleanup_task_state(self, task_id):
        """清理任务状态"""
        if task_id in self._audio_task_states:
            del self._audio_task_states[task_id]

    @property
    def interrupt_task_id(self):
        return self._interrupt_task_id

    @interrupt_task_id.setter
    def interrupt_task_id(self, value):
        self._interrupt_task_id = value

    def reset_interrupt_task_id(self):
        self.interrupt_task_id = ''
