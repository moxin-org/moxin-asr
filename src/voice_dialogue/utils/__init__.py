from voice_dialogue.config.paths import PROJECT_ROOT
from .cache import LRUCacheDict
from .download_utils import (
    download_model_from_huggingface, download_file_from_huggingface, check_file_exists_on_huggingface,
    download_lora_from_huggingface, download_civitai_file
)
from .logger import logger
from .strings import remove_emojis
from .system import get_system_language, get_system_info

# 导入HParams类，解决moyoyo_tts的序列化问题
try:
    import sys
    from pathlib import Path

    # 添加third_party路径
    third_party_path = PROJECT_ROOT / "third_party"

    if str(third_party_path) not in sys.path:
        sys.path.insert(0, str(third_party_path))

    from moyoyo_tts.utils import HParams

except ImportError:
    # 如果导入失败，创建一个简单的HParams类
    class HParams:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                if type(v) == dict:
                    v = HParams(**v)
                self[k] = v

        def keys(self):
            return self.__dict__.keys()

        def items(self):
            return self.__dict__.items()

        def values(self):
            return self.__dict__.values()

        def __len__(self):
            return len(self.__dict__)

        def __getitem__(self, key):
            return getattr(self, key)

        def __setitem__(self, key, value):
            return setattr(self, key, value)

        def __contains__(self, key):
            return key in self.__dict__

        def __repr__(self):
            return self.__dict__.__repr__()

__all__ = (
    'remove_emojis',
    'download_model_from_huggingface',
    'download_file_from_huggingface',
    'check_file_exists_on_huggingface',
    'download_lora_from_huggingface',
    'download_civitai_file',
    'LRUCacheDict',
    'get_system_language',
    'get_system_info',
    'logger',
)
