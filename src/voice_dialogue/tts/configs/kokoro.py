from ..models.kokoro import KokoroTTSConfig

ENGLISH_MODEL_FILES = {
    'model': 'kokoro-v1.0.int8.onnx',
    'voice': 'voices-v1.0.bin'
}

CHINESE_MODEL_FILES = {
    'model': 'kokoro-v1.1-zh.onnx',
    'voice': 'voices-v1.1-zh.bin',
    'vocab_config': 'config.json'
}

KOKORO_TTS_CONFIGS = [
    # {
    #     'character_name': 'Heart',
    #     'cover_image': '',
    #     'description': 'Heart是一个温暖亲切的英语女性语音，声音富有感情色彩，适合情感表达和温馨内容的语音合成。',
    #     'file_size': '',
    #     'is_chinese_voice': False,
    #     'inference_parameters': {
    #         'voice': 'af_heart',
    #         'speed': 1.0,
    #         'is_phonemes': True,
    #     },
    #     'model_files': ENGLISH_MODEL_FILES,
    # },
    # {
    #     'character_name': 'Bella',
    #     'cover_image': '',
    #     'description': 'Bella是一个优质的英语女性语音，具有清晰自然的发音和良好的表现力，适合各种英语内容的语音合成。',
    #     'file_size': '',
    #     'is_chinese_voice': False,
    #     'inference_parameters': {
    #         'voice': 'af_bella',
    #         'speed': 1.0,
    #         'is_phonemes': True,
    #     },
    #     'model_files': ENGLISH_MODEL_FILES,
    # },
    # {
    #     'character_name': 'Nicole',
    #     'cover_image': '',
    #     'description': 'Nicole是一个高质量的英语女性语音，发音清晰准确，语调自然流畅。',
    #     'file_size': '',
    #     'is_chinese_voice': False,
    #     'inference_parameters': {
    #         'voice': 'af_nicole',
    #         'speed': 1.0,
    #         'is_phonemes': True,
    #     },
    #     'model_files': ENGLISH_MODEL_FILES,
    # },
]


def get_kokoro_configs() -> list[KokoroTTSConfig]:
    return [KokoroTTSConfig(**config) for config in KOKORO_TTS_CONFIGS]
