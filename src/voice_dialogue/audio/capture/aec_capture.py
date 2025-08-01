import ctypes
import time
from multiprocessing import Queue

from voice_dialogue.config.paths import LIBRARIES_PATH
from voice_dialogue.utils.logger import logger
from .base_capture import BaseCapture


class AecCapture(BaseCapture):
    """
    使用 macOS 原生库进行支持 AEC 的音频捕获策略。
    """

    def __init__(self, audio_frames_queue: Queue, **kwargs):
        super().__init__(audio_frames_queue=audio_frames_queue, **kwargs)

    def _load_library(self):
        """加载并配置 AEC 原生库。"""
        try:
            audio_recorder = ctypes.CDLL(LIBRARIES_PATH / 'libAudioCapture.dylib')
            audio_recorder.getAudioData.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_bool)]
            audio_recorder.getAudioData.restype = ctypes.POINTER(ctypes.c_ubyte)
            audio_recorder.freeAudioData.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
            return audio_recorder
        except Exception as e:
            logger.error(f"加载 AEC 动态库失败: {e}")
            raise

    def _capture_loop(self, audio_recorder):
        """AEC 音频捕获的主循环。"""
        logger.info("使用 AEC 音频捕获器开始采集...")
        audio_recorder.startRecord()
        self.is_ready = True

        while not self.is_exited:
            size = ctypes.c_int(0)
            is_voice_active = ctypes.c_bool(False)
            # 从原生库获取音频数据
            data_ptr = audio_recorder.getAudioData(ctypes.byref(size), ctypes.byref(is_voice_active))

            if data_ptr and size.value > 0:
                audio_data = bytes(data_ptr[: size.value])

                if not self.is_paused:
                    # 将音频帧和语音活动状态一同放入队列
                    self.audio_frames_queue.put((audio_data, is_voice_active.value))

                # 释放原生库分配的内存
                audio_recorder.freeAudioData(data_ptr)
            else:
                # 无数据时短暂休眠，避免CPU空转
                time.sleep(0.01)

    def _cleanup(self, audio_recorder):
        """清理 AEC 资源。"""
        logger.info("停止 AEC 音频采集...")
        if not audio_recorder:
            return
        audio_recorder.stopRecord()

    def run(self):
        """
        线程主循环，执行 AEC 音频捕获。
        """
        audio_recorder = None
        try:
            audio_recorder = self._load_library()
            self._capture_loop(audio_recorder)
        except Exception as e:
            logger.error(f'回声消除音频捕获器运行时发生错误: {e}')
            # 如果 AEC 失败，这里可以考虑触发一个事件或回退机制，但目前只记录错误
        finally:
            self._cleanup(audio_recorder)
