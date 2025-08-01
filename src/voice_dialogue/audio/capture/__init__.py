"""
音频捕获模块门面。

根据配置选择并管理具体的音频捕获策略。
"""
from multiprocessing import Queue

from voice_dialogue.utils.logger import logger
from .aec_capture import AecCapture
from .pyaudio_capture import PyAudioCapture


class AudioCapture:
    """
    音频捕获器门面 (Facade)。

    根据配置选择并管理具体的音频捕获策略（PyAudio 或 AEC）。
    为上层应用提供统一的、简化的音频捕获接口。
    它不是一个线程，而是线程安全策略的管理者。
    """

    def __init__(
            self,
            audio_frames_queue: Queue,
            enable_echo_cancellation: bool = True,
    ):
        """
        初始化音频捕获器。

        Args:
            audio_frames_queue (Queue): 用于存放捕获的音频帧的队列。
            enable_echo_cancellation (bool): 是否启用回声消除功能。
                                             若为 True，则使用 AEC 原生库；
                                             否则，使用 PyAudio。
        """
        self._strategy = None
        try:
            if enable_echo_cancellation:
                self._strategy = AecCapture(audio_frames_queue=audio_frames_queue)
            else:
                self._strategy = PyAudioCapture(audio_frames_queue=audio_frames_queue)
            logger.info(f"音频捕获策略已选择: {self._strategy.__class__.__name__}")
        except Exception as e:
            logger.error(
                f"初始化 {AecCapture.__name__ if enable_echo_cancellation else PyAudioCapture.__name__} 失败: {e}, 将回退到 PyAudio。")
            # 只有在尝试 AEC 失败时才回退
            if not isinstance(self._strategy, PyAudioCapture):
                self._strategy = PyAudioCapture(audio_frames_queue=audio_frames_queue)
                logger.info(f"已回退到音频捕获策略: {self._strategy.__class__.__name__}")

    def start(self):
        """启动音频捕获线程。"""
        self._strategy.start()

    def stop(self):
        """停止音频捕获线程。"""
        self._strategy.exit()

    def pause(self):
        """暂停音频捕获。"""
        self._strategy.pause()

    def resume(self):
        """恢复音频捕获。"""
        self._strategy.resume()

    @property
    def is_paused(self) -> bool:
        """检查捕获器是否已暂停。"""
        return self._strategy.is_paused

    @property
    def is_ready(self) -> bool:
        """检查捕获线程是否已准备就绪。"""
        return self._strategy.is_ready

    def is_alive(self):
        return self._strategy.is_alive()
