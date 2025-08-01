import threading
from abc import ABC, abstractmethod
from multiprocessing import Queue

from voice_dialogue.core.base import BaseThread


class BaseCapture(BaseThread, ABC):
    """
    抽象音频捕获器基类。

    定义了所有音频捕获策略应遵循的通用接口。
    """

    def __init__(
            self,
            audio_frames_queue: Queue,
            group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None
    ):
        """
        初始化音频捕获器。

        Args:
            audio_frames_queue (Queue): 用于存放捕获的音频帧的队列。
        """
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.audio_frames_queue = audio_frames_queue
        self._pause_event = threading.Event()

    @property
    def is_paused(self) -> bool:
        """检查捕获器是否已暂停。"""
        return self._pause_event.is_set()

    def pause(self):
        """暂停音频捕获。"""
        self._pause_event.set()

    def resume(self):
        """恢复音频捕获。"""
        self._pause_event.clear()

    @abstractmethod
    def run(self):
        """
        线程主循环。

        子类必须实现此方法以提供具体的音频捕获逻辑。
        """
        raise NotImplementedError
