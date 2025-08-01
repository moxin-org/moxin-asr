from .base import ASRInterface

__all__ = ['ASRInterface']

try:
    from .funasr import FunASRClient

    __all__.append('FunASRClient')
except ImportError as e:
    from voice_dialogue.utils.logger import logger

    logger.warning(f"Failed to import some FunASR implementations: {e}")

try:
    from .whisper import WhisperCppClient

    __all__.append('WhisperCppClient')
except ImportError as e:
    from voice_dialogue.utils.logger import logger

    logger.warning(f"Failed to import some Whisper implementations: {e}")
