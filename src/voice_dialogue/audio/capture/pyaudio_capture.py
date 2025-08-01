from multiprocessing import Queue

import pyaudio

from voice_dialogue.utils.logger import logger
from .base_capture import BaseCapture


class PyAudioCapture(BaseCapture):
    """
    使用 PyAudio 进行标准的音频采集策略。
    """

    def __init__(self, audio_frames_queue: Queue, **kwargs):
        super().__init__(audio_frames_queue=audio_frames_queue, **kwargs)

    def _init_pyaudio(self):
        """初始化 PyAudio 并返回实例和配置。"""
        p = pyaudio.PyAudio()
        chunk = 1024
        sample_rate = 16000
        return p, chunk, sample_rate

    def _open_stream(self, p, chunk, sample_rate):
        """打开 PyAudio 音频流。"""
        return p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk,
        )

    def _capture_loop(self, stream, chunk):
        """PyAudio 音频捕获的主循环。"""
        logger.info("使用 PyAudio 开始音频采集...")
        self.is_ready = True

        while not self.is_exited:
            data = stream.read(chunk, exception_on_overflow=False)
            if data is None:
                continue

            if self.is_paused:
                continue

            self.audio_frames_queue.put(data)

    def _cleanup(self, stream, p):
        """清理 PyAudio 资源。"""
        logger.info("停止 PyAudio 音频采集...")
        stream.stop_stream()
        stream.close()
        p.terminate()

    def run(self):
        """
        线程主循环，执行 PyAudio 音频采集。
        """
        p, chunk, sample_rate = self._init_pyaudio()
        stream = None
        try:
            stream = self._open_stream(p, chunk, sample_rate)
            self._capture_loop(stream, chunk)
        except Exception as e:
            logger.error(f'PyAudio 音频捕获器运行时发生错误: {e}')
        finally:
            if stream:
                self._cleanup(stream, p)
