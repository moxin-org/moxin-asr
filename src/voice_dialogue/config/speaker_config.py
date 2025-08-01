"""
TTS说话人配置管理

提供说话人配置的查找、映射和管理功能
"""

from voice_dialogue.tts.models import tts_config_registry


def get_tts_config_by_speaker_name(speaker_name: str):
    """
    根据说话人名称获取TTS配置

    支持中文名称和英文名称，优先匹配中文名称映射，
    如果找不到则直接使用英文名称搜索

    Args:
        speaker_name (str): 说话人名称

    Returns:
        BaseTTSConfig: TTS配置，如果找不到则返回None
    """
    # 中文名称到英文名称的映射（保持向后兼容）
    chinese_to_english_mapping = {
        '罗翔': 'Luo Xiang',
        '马保国': 'Ma Baoguo',
        '沈逸': 'Shen Yi',
        '杨幂': 'Yang Mi',
        '周杰伦': 'Zhou Jielun',
        '马云': 'Ma Yun',
    }

    # 首先尝试中文名称映射
    english_name = chinese_to_english_mapping.get(speaker_name, speaker_name)

    # 获取所有可用配置
    all_configs = tts_config_registry.get_all_configs()

    # 搜索匹配的配置
    for config in all_configs:
        if config.character_name == english_name:
            return config

    # 如果通过映射找不到，尝试直接匹配输入的名称
    if speaker_name != english_name:
        for config in all_configs:
            if config.character_name == speaker_name:
                return config

    return None


def get_available_speaker_names():
    """
    获取所有可用的说话人名称列表

    Returns:
        list[str]: 包含中文显示名称和英文原始名称的列表
    """
    # 中文显示名称映射
    english_to_chinese_mapping = {
        'Luo Xiang': '罗翔',
        'Ma Baoguo': '马保国',
        'Shen Yi': '沈逸',
        'Yang Mi': '杨幂',
        'Zhou Jielun': '周杰伦',
        'Ma Yun': '马云',
    }

    all_configs = tts_config_registry.get_all_configs()
    speaker_names = []

    for config in all_configs:
        # 优先显示中文名称
        chinese_name = english_to_chinese_mapping.get(config.character_name)
        if chinese_name:
            speaker_names.append(chinese_name)
        else:
            # 如果没有中文映射，使用英文原名
            speaker_names.append(config.character_name)

    return sorted(speaker_names)


def update_argument_parser_speaker_choices():
    """
    动态更新命令行参数解析器中的说话人选项

    Returns:
        list[str]: 可用的说话人选择列表
    """
    return get_available_speaker_names()
