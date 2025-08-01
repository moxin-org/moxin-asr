"""
语音状态监控模块

该模块包含 SpeechStateMonitor 类，用于实时监控用户的语音状态，
包括语音活动检测、静音检测、语音任务管理等功能。
"""

import time
import uuid
from multiprocessing import Queue
from queue import Empty

import librosa
import numpy as np

from voice_dialogue.audio.vad import SileroVAD
from voice_dialogue.core.base import BaseThread
from voice_dialogue.core.constants import (
    voice_state_manager, silence_over_threshold_event, user_still_speaking_event, session_manager
)
from voice_dialogue.core.enums import AudioState
from voice_dialogue.models.voice_task import VoiceTask
from voice_dialogue.services.utils import normalize_audio_frame, calculate_audio_duration
from voice_dialogue.utils.logger import logger


class SpeechMonitorConfig:
    """语音监控配置类"""
    MIN_AUDIO_AMPLITUDE = 0.01  # 最小音频振幅阈值
    QUEUE_TIMEOUT = 0.1  # 队列获取超时时间（秒）

    # 时间阈值（毫秒）
    ACTIVE_FRAME_THRESHOLD = 0.1 * 1000  # 连续活跃帧数阈值
    USER_SILENCE_THRESHOLD = 1 * 1000  # 用户静音阈值
    SILENCE_THRESHOLD = 0.3 * 1000  # 静音检测阈值
    AUDIO_FRAMES_THRESHOLD = 5 * 1000  # 音频帧时长阈值


class SpeechStateMonitor(BaseThread):
    """
    语音状态监控器
    
    负责实时监控用户的语音状态，包括：
    - 语音活动检测
    - 静音检测和处理
    - 语音任务的创建和管理
    - 音频帧的缓存和处理
    """

    def __init__(
            self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None,
            audio_frame_queue: Queue,
            user_voice_queue: Queue,
            enable_vad: bool = False,
    ):
        """
        初始化语音状态监控器
        
        Args:
            audio_frame_queue: 音频帧队列
            user_voice_queue: 用户语音队列
            enable_vad: 是否启用语音活动检测
        """
        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self.audio_frame_queue = audio_frame_queue
        self.user_voice_queue = user_voice_queue
        self.sample_rate = 16000
        self._enable_vad = enable_vad

        self._vad_instance = None
        if self._enable_vad:
            self._vad_instance = SileroVAD()

        # 配置参数
        self.config = SpeechMonitorConfig()

        # 重置状态
        self._reset_monitoring_state()

    def _reset_monitoring_state(self):
        """重置监控状态"""
        self.silence_audio_frame_count = 0
        self.active_audio_frame_duration = 0
        self.user_silence_duration = 0
        self.task_id = None

    def _initialize_new_task(self):
        """初始化新的语音任务"""
        if not voice_state_manager.task_id:
            voice_state_manager.create_task_id()
            voice_state_manager.reset_interrupt_task_id()

        self.task_id = voice_state_manager.task_id
        silence_over_threshold_event.clear()
        user_still_speaking_event.clear()

        # 返回初始状态
        return np.array([]), False, True  # audio_frames, is_audio_sent_for_processing, is_audio_frames_empty

    def _handle_task_cleanup(self):
        """处理任务清理"""
        if voice_state_manager.get_audio_task_state(self.task_id) == AudioState.DROP:
            voice_state_manager.cleanup_task_state(self.task_id)
            return True
        return False

    def _check_silence_threshold(self):
        """检查用户静音阈值"""
        if self.user_silence_duration >= self.config.USER_SILENCE_THRESHOLD:
            silence_over_threshold_event.set()

    def _normalize_audio_frame(self, data: bytes) -> np.ndarray:
        """将 int16 格式的音频字节数据转换为 [-1.0, 1.0] 范围的 numpy 浮点数组。"""
        return normalize_audio_frame(data)

    def _detect_speech(self, audio_frame: np.ndarray) -> bool:
        return self._vad_instance.is_voice_active(audio_frame, self.sample_rate)

    def _get_audio_frame_from_queue(self):
        """从队列获取音频帧"""
        try:
            if self._enable_vad:
                data = self.audio_frame_queue.get(block=True, timeout=self.config.QUEUE_TIMEOUT)
                audio_frame = self._normalize_audio_frame(data)
                is_voice_active = self._detect_speech(audio_frame)
            else:
                data, is_voice_active = self.audio_frame_queue.get(block=True, timeout=self.config.QUEUE_TIMEOUT)
                audio_frame = self._normalize_audio_frame(data)
            return audio_frame, is_voice_active
        except Empty:
            return None, None

    def _calculate_frame_duration_ms(self, audio_frame):
        """计算音频帧时长（毫秒）"""
        return calculate_audio_duration(audio_data=audio_frame, sample_rate=self.sample_rate) * 1000

    def _process_active_voice_frame(self, audio_frame: np.ndarray):
        """
        处理活跃语音帧
        
        Args:
            audio_frame: 音频帧数据
            
        Returns:
            bool: 是否为有效的活跃语音帧
        """
        if np.max(audio_frame) <= self.config.MIN_AUDIO_AMPLITUDE:
            return False

        # 重置静音计时
        self.user_silence_duration = 0
        duration = self._calculate_frame_duration_ms(audio_frame)
        self.active_audio_frame_duration += duration

        # 检查是否需要中断当前任务
        if self.active_audio_frame_duration > self.config.ACTIVE_FRAME_THRESHOLD:
            voice_state_manager.interrupt_task_id = self.task_id

        return True

    def _process_silence_frame(self, audio_frame, audio_frames, is_audio_frames_empty, is_audio_sent_for_processing):
        """
        处理静音帧
        
        Args:
            audio_frame: 音频帧数据
            audio_frames: 当前音频帧缓存
            is_audio_frames_empty: 音频帧缓存是否为空
            is_audio_sent_for_processing: 是否已发送音频进行处理
            
        Returns:
            tuple: (更新后的音频帧缓存, 是否需要继续处理)
        """
        self.active_audio_frame_duration = 0
        duration = self._calculate_frame_duration_ms(audio_frame)

        if is_audio_frames_empty:
            # 处理空缓存的静音帧
            audio_frames = np.append(audio_frames, audio_frame)

            # 维持固定长度的静音缓存
            silence_duration = librosa.get_duration(y=audio_frames, sr=self.sample_rate) * 1000
            if silence_duration >= self.config.SILENCE_THRESHOLD:
                cached_slice = len(audio_frames) - int(self.config.SILENCE_THRESHOLD * (self.sample_rate / 1000))
                audio_frames = audio_frames[cached_slice:]

            user_still_speaking_event.clear()
            if is_audio_sent_for_processing:
                self.user_silence_duration += duration

            return audio_frames, True  # 需要继续处理

        # 处理非空缓存的静音帧
        self.user_silence_duration += duration
        return audio_frames, False  # 不需要继续处理

    def _update_speaking_state(self, is_voice_active, is_audio_sent_for_processing):
        """更新用户说话状态"""
        if is_voice_active and is_audio_sent_for_processing:
            user_still_speaking_event.set()

    def _create_voice_task(self, audio_frames):
        """
        创建语音任务
        
        Args:
            audio_frames: 音频帧数据
            
        Returns:
            VoiceTask: 创建的语音任务
        """
        voice_task = VoiceTask(id=self.task_id, session_id=session_manager.current_id)
        voice_task.answer_id = f'{uuid.uuid4()}'
        voice_task.user_voice = audio_frames.copy()
        voice_task.send_time = time.time()

        # 检查音频时长是否超过阈值
        audio_duration = librosa.get_duration(y=audio_frames, sr=self.sample_rate) * 1000
        if audio_duration >= self.config.AUDIO_FRAMES_THRESHOLD:
            voice_task.is_over_audio_frames_threshold = True

        return voice_task

    def _should_send_voice_task(self, is_audio_sent_for_processing):
        """判断是否应该发送语音任务"""
        return self.is_user_in_silence() and not is_audio_sent_for_processing

    def is_user_in_silence(self):
        """检查用户是否处于静音状态"""
        return self.user_silence_duration >= self.config.SILENCE_THRESHOLD

    def run(self):
        """
        主运行循环 - 监控语音状态并处理音频帧
        """

        self.is_ready = True

        # 初始化状态变量
        audio_frames = np.array([])
        is_audio_sent_for_processing = False
        is_audio_frames_empty = True

        while not self.is_exited:
            try:
                # 1. 管理任务生命周期
                self.task_id = voice_state_manager.task_id
                if not self.task_id:
                    audio_frames, is_audio_sent_for_processing, is_audio_frames_empty = self._initialize_new_task()

                # 2. 处理任务清理
                if self._handle_task_cleanup():
                    is_audio_sent_for_processing = False
                    continue

                # 3. 检查静音阈值
                self._check_silence_threshold()

                # 4. 获取音频帧
                audio_frame, is_voice_active = self._get_audio_frame_from_queue()
                if audio_frame is None and is_voice_active is None:
                    continue

                # 5. 处理空音频帧
                if audio_frame is None:
                    if is_audio_sent_for_processing:
                        self.silence_audio_frame_count += 1
                    continue

                # 6. 处理音频帧内容
                if is_voice_active:
                    # 处理活跃语音帧
                    if self._process_active_voice_frame(audio_frame):
                        is_audio_frames_empty = False
                        audio_frames = np.append(audio_frames, audio_frame)
                else:
                    # 处理静音帧
                    audio_frames, should_continue = self._process_silence_frame(
                        audio_frame, audio_frames, is_audio_frames_empty, is_audio_sent_for_processing
                    )
                    if should_continue:
                        continue

                    is_audio_frames_empty = False
                    audio_frames = np.append(audio_frames, audio_frame)

                # 7. 更新说话状态
                self._update_speaking_state(is_voice_active, is_audio_sent_for_processing)

                # 8. 检查是否需要发送语音任务
                if self._should_send_voice_task(is_audio_sent_for_processing):
                    voice_task = self._create_voice_task(audio_frames)
                    self.user_voice_queue.put(voice_task.model_copy(deep=True))

                    # 更新状态
                    is_audio_sent_for_processing = True
                    user_still_speaking_event.clear()

                    # 如果音频超过时长阈值，重置缓存
                    if hasattr(voice_task, 'is_over_audio_frames_threshold') and \
                            voice_task.is_over_audio_frames_threshold:
                        audio_frames = np.array([])
                        is_audio_frames_empty = True

            except Exception as e:
                # 错误处理，防止线程崩溃
                logger.error(f"SpeechStateMonitor 处理错误: {e}")
                time.sleep(0.1)  # 避免错误循环
                continue
