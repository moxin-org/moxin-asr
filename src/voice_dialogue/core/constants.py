import asyncio
import multiprocessing
import threading
from collections import OrderedDict

from voice_dialogue.utils.cache import LRUCacheDict
from .session_manager import SessionIdManager
from .state_manager import VoiceStateManager

# ======================= 应用配置常量 =======================

# 全局调试模式状态
DEBUG_MODE = False

def set_debug_mode(enabled: bool):
    """设置全局调试模式"""
    global DEBUG_MODE
    DEBUG_MODE = enabled

def is_debug_mode() -> bool:
    """检查是否启用了调试模式"""
    return DEBUG_MODE

# ======================= 音频配置常量 =======================

# 音频采样率与窗口大小映射配置
SAMPLE_RATE_WINDOW_SIZE_MAPPING = {
    # 电话语音常用采样率，窗口大小选择512便于在较低采样率下进行相对精细的短时分析
    8000: 512,
    # 常见的语音处理采样率，例如语音识别等场景，512的窗口大小在这个采样率下能较好地平衡频率分辨率和时间分辨率
    16000: 512,
    # 一些音频录制设备的标准采样率，1024的窗口大小可以获取更宽的频率范围信息，适合音频分析等应用
    44100: 1024,
    # 专业音频领域常用采样率，更高的采样率需要适当增大窗口大小以充分利用高分辨率优势，2048的窗口大小有助于提取更丰富的音频特征
    48000: 2048,
    # 高清音频采样率，对于这样高的采样率，更大的窗口大小可以让我们在频域分析时有更好的表现，这里选择4096作为窗口大小
    96000: 4096,
    # 超高清音频采样率，对应更大的窗口尺寸便于在处理这种高质量音频时获得更精准的频谱等信息
    192000: 8192
}

# 默认音频配置
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_WINDOW_SIZE = 512

# ======================= 队列变量 =======================

# 音频处理相关队列
audio_frames_queue = multiprocessing.Queue()
user_voice_queue = multiprocessing.Queue()
transcribed_text_queue = multiprocessing.Queue()
text_input_queue = multiprocessing.Queue()
audio_output_queue = multiprocessing.Queue()
websocket_message_queue = asyncio.Queue()

# ======================= 全局状态实例 =======================

# 语音状态管理器实例
voice_state_manager = VoiceStateManager()

# 会话缓存
chat_history_cache: dict[str, OrderedDict] = {}
session_manager: SessionIdManager = SessionIdManager()
dropped_audio_cache = LRUCacheDict(maxsize=50)

# ======================= 线程事件对象 =======================

# 音频播放相关事件
audio_playing_event = threading.Event()
silence_over_threshold_event = threading.Event()
user_still_speaking_event = threading.Event()
user_interrupting_playback_event = threading.Event()

# 中断任务ID
interrupt_task_id = ''
