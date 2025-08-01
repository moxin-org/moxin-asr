from typing import Tuple, Optional

import numpy as np
from kokoro_onnx import Kokoro

from voice_dialogue.tts.configs.kokoro import KokoroTTSConfig
from voice_dialogue.tts.manager import tts_tables
from voice_dialogue.tts.runtime.interface import TTSInterface
from voice_dialogue.utils.logger import logger


@tts_tables.register("tts_classes", "kokoro")
class KokoroTTS(TTSInterface):
    def __init__(self, config: KokoroTTSConfig):
        super().__init__(config)
        self.tts_model: Optional[Kokoro] = None
        self.espeak_ng = None

    def setup(self, **kwargs) -> None:
        if self.config.is_chinese_voice:
            self.tts_model = Kokoro(
                model_path=self.config.model_path,
                voices_path=self.config.voices_path,
                vocab_config=self.config.vocab_config_path,
            )
            from misaki import zh
            self.espeak_ng = zh.ZHG2P(version="1.1")
        else:
            self.tts_model = Kokoro(
                model_path=self.config.model_path,
                voices_path=self.config.voices_path
            )

            from misaki import en, espeak
            fallback = espeak.EspeakFallback(british=False)
            self.espeak_ng = en.G2P(trf=False, british=False, fallback=fallback)

    def warmup(self, warmup_steps: int = 1) -> None:
        logger.info('[INFO:] Warming up Kokoro TTS engine...')
        warmup_texts = ['Warming up TTS engine.', '预热文字转音频引擎。']
        for _ in range(warmup_steps):
            for warmup_text in warmup_texts:
                self.synthesize(warmup_text)
        logger.info('[INFO:] Warm up Kokoro TTS engine finished.')

    def synthesize(self, text: str, **kwargs) -> Tuple[np.ndarray, int]:
        phonemes, _ = self.espeak_ng(text)
        samples, sample_rate = self.tts_model.create(phonemes, **self.config.inference_parameters.model_dump())
        return samples, sample_rate
