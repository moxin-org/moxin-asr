import re
import sys
import typing
from typing import Tuple

import numpy as np

from voice_dialogue.config.paths import load_third_party
from voice_dialogue.tts.manager import tts_tables
from voice_dialogue.tts.models.moyoyo import MoYoYoTTSConfig
from voice_dialogue.tts.runtime.interface import TTSInterface
from voice_dialogue.utils.logger import logger

load_third_party()

from moyoyo_tts import TTSModule, TTS_Config
from moyoyo_tts.utils import HParams

if "utils" not in sys.modules:
    class GPTSoVITSFixedUtilsModule:
        HParams = HParams


    sys.modules['utils'] = GPTSoVITSFixedUtilsModule


@tts_tables.register("tts_classes", "moyoyo")
class MoYoYoTTS(TTSInterface):
    """MoYoYo TTS实现"""

    def __init__(self, config: MoYoYoTTSConfig):
        super().__init__(config)
        self.tts_module: typing.Optional[TTSModule] = None

    def setup(self, **kwargs) -> None:
        """设置TTS模块"""
        tts_config = TTS_Config(self.config.get_runtime_config())
        self.tts_module = TTSModule(tts_config)
        self.tts_module.setup_inference_params(
            ref_audio=self.config.reference_audio_path,
            parallel_infer=False,
            **self.config.inference_parameters.model_dump()
        )
        self.is_ready = True

    def warmup(self, warmup_steps: int = 1) -> None:
        """预热TTS引擎"""
        logger.info('[INFO:] Warming up MoYoYo TTS engine...')
        warmup_texts = ['Warming up TTS engine.', '预热文字转音频引擎。']
        for _ in range(warmup_steps):
            for warmup_text in warmup_texts:
                self.tts_module.generate_audio(warmup_text, warmup=True)
        logger.info('[INFO:] Warm up MoYoYo TTS engine finished.')

    def synthesize(self, text: str, **kwargs) -> Tuple[np.ndarray, int]:
        """合成语音"""
        if not self.is_ready:
            raise RuntimeError("TTS module is not ready. Please call setup() first.")

        text = self._clean_text(text)

        (sample_rate, audio_data), *_ = self.tts_module.generate_audio(text)
        return audio_data, sample_rate

    def _clean_text(self, text: str) -> str:
        """去除文本中的中英文标点符号。"""
        # 去除中英文标点符号，保留字母、数字、下划线、中文和空格
        return re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
