import typing
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from voice_dialogue.utils.logger import logger


class TTSConfigType(Enum):
    """TTS引擎类型枚举"""
    MOYOYO = 'moyoyo'
    KOKORO = 'kokoro'


class VoiceModelStatus(Enum):
    """声音模型状态枚举"""
    NOT_DOWNLOADED = 'not_downloaded'
    DOWNLOADING = 'downloading'
    DOWNLOADED = 'downloaded'
    FAILED = 'failed'


class BaseTTSConfig(BaseModel, ABC):
    """TTS配置基类"""
    tts_type: TTSConfigType
    character_name: str
    cover_image: str
    description: str
    file_size: str
    is_chinese_voice: bool

    @abstractmethod
    def get_model_storage_path(self) -> Path:
        """获取模型存储路径"""
        pass

    @abstractmethod
    def is_model_complete(self) -> bool:
        """检查模型文件是否完整"""
        pass

    @abstractmethod
    def download_model(self, progress_callback: typing.Callable = None):
        """下载模型"""
        pass

    @abstractmethod
    def delete_model(self):
        """删除模型"""
        pass


class TTSConfigRegistry:
    """TTS注册表，管理所有TTS引擎和配置"""

    def __init__(self):
        self._configs: dict[str, BaseTTSConfig] = {}
        self._priority_order = {
            TTSConfigType.KOKORO: 1,
            TTSConfigType.MOYOYO: 2,
        }

    def register_config(self, config: BaseTTSConfig):
        """注册TTS配置"""
        key = f"{config.tts_type.value}:{config.character_name}"
        self._configs[key] = config

    def get_config(self, tts_type: TTSConfigType, character_name: str) -> BaseTTSConfig:
        """获取指定配置"""
        key = f"{tts_type.value}:{character_name}"
        return self._configs.get(key)

    def get_configs_by_type(self, tts_type: TTSConfigType) -> list[BaseTTSConfig]:
        """获取指定类型的所有配置"""
        return [config for config in self._configs.values()
                if config.tts_type == tts_type]

    def get_all_configs(self) -> list[BaseTTSConfig]:
        """获取所有配置"""
        return list(self._configs.values())

    def get_default_config(self, user_language: typing.Optional[typing.Literal['zh', 'en']] = None) -> typing.Optional[
        BaseTTSConfig]:
        """
        获取默认的TTS配置
        
        选择逻辑：
        1. 根据用户语言偏好选择对应的语音类型（中文/非中文）
        2. 优先选择已下载完整的模型
        3. 按照预定义的优先级顺序选择TTS类型
        4. 在同类型中优先选择匹配语言的语音
        5. 如果都没有完整模型，返回优先级最高且语言匹配的配置
        
        Args:
            user_language: 用户语言偏好，'zh'为中文，'en'为英文，None则自动检测系统语言
            
        Returns:
            BaseTTSConfig: 默认配置，如果没有任何配置则返回None
        """
        try:
            # 如果没有指定用户语言，则自动检测系统语言
            if user_language is None:
                try:
                    from utils.system import get_system_language
                    user_language = get_system_language()
                    logger.info(f"自动检测到系统语言: {user_language}")
                except ImportError:
                    logger.warning("无法导入系统语言检测模块，使用默认语言 'zh'")
                    user_language = 'zh'
                except Exception as e:
                    logger.warning(f"系统语言检测失败: {e}，使用默认语言 'zh'")
                    user_language = 'zh'

            all_configs = self.get_all_configs()

            if not all_configs:
                logger.warning("没有找到任何TTS配置")
                return None

            # 确定语音偏好：中文系统偏好中文语音，非中文系统偏好非中文语音
            prefer_chinese_voice = (user_language == 'zh')
            logger.info(f"用户语言: {user_language}, 语音偏好: {'中文语音' if prefer_chinese_voice else '非中文语音'}")

            # 首先尝试找到已完整下载且语言匹配的配置
            complete_configs = [config for config in all_configs if config.is_model_complete()]

            if complete_configs:
                # 按语言偏好和优先级排序已完整的配置
                selected_config = self._select_config_by_priority_and_language(complete_configs, prefer_chinese_voice)
                logger.info(
                    f"选择已完整的默认TTS配置: {selected_config.tts_type.value}:{selected_config.character_name} "
                    f"(语音类型: {'中文' if selected_config.is_chinese_voice else '非中文'})")
                return selected_config

            # 如果没有完整的配置，选择优先级最高且语言匹配的配置
            logger.warning("没有找到完整下载的TTS模型，选择优先级最高且语言匹配的配置")
            fallback_config = self._select_config_by_priority_and_language(all_configs, prefer_chinese_voice)
            logger.info(f"使用备选默认TTS配置: {fallback_config.tts_type.value}:{fallback_config.character_name} "
                        f"(语音类型: {'中文' if fallback_config.is_chinese_voice else '非中文'})")
            return fallback_config

        except Exception as e:
            logger.error(f"获取默认TTS配置时发生错误: {e}", exc_info=True)
            return None

    def _select_config_by_priority_and_language(
            self,
            configs: list[BaseTTSConfig],
            prefer_chinese_voice: bool
    ) -> BaseTTSConfig:
        """
        按优先级和语言偏好选择配置
        
        Args:
            configs: 配置列表
            prefer_chinese_voice: 是否偏好中文语音
            
        Returns:
            BaseTTSConfig: 选中的配置
        """
        if not configs:
            raise ValueError("配置列表不能为空")

        # 按优先级和语言偏好排序
        def sort_key(config: BaseTTSConfig):
            # 优先级权重（数字越小优先级越高）
            tts_priority = self._priority_order.get(config.tts_type, 999)

            character_priority = -config.priority

            # 语言匹配加分
            # 如果偏好中文语音且配置是中文语音，或者偏好非中文语音且配置是非中文语音，则加分
            language_match = (prefer_chinese_voice == config.is_chinese_voice)
            language_bonus = 0 if language_match else 1

            # 角色名称作为最后的排序条件
            return (language_bonus, tts_priority, character_priority, config.character_name)

        sorted_configs = sorted(configs, key=sort_key)
        return sorted_configs[0]

    def get_recommended_configs(self, max_count: int = 3,
                                user_language: typing.Optional[typing.Literal['zh', 'en']] = None) -> list[
        BaseTTSConfig]:
        """
        获取推荐的TTS配置列表
        
        Args:
            max_count: 最大返回数量
            user_language: 用户语言偏好，'zh'为中文，'en'为英文，None则自动检测系统语言
            
        Returns:
            list[BaseTTSConfig]: 推荐配置列表
        """
        try:
            # 如果没有指定用户语言，则自动检测系统语言
            if user_language is None:
                try:
                    from utils.system import get_system_language
                    user_language = get_system_language()
                except (ImportError, Exception):
                    user_language = 'zh'

            all_configs = self.get_all_configs()

            if not all_configs:
                return []

            prefer_chinese_voice = (user_language == 'zh')

            # 优先返回已完整下载的配置
            complete_configs = [config for config in all_configs if config.is_model_complete()]

            if complete_configs:
                sorted_configs = sorted(complete_configs,
                                        key=lambda c: (self._priority_order.get(c.tts_type, 999),
                                                       0 if (prefer_chinese_voice == c.is_chinese_voice) else 1,
                                                       c.character_name))
                return sorted_configs[:max_count]

            # 如果没有完整配置，返回按优先级和语言偏好排序的配置
            sorted_configs = sorted(all_configs,
                                    key=lambda c: (self._priority_order.get(c.tts_type, 999),
                                                   0 if (prefer_chinese_voice == c.is_chinese_voice) else 1,
                                                   c.character_name))
            return sorted_configs[:max_count]

        except Exception as e:
            logger.error(f"获取推荐TTS配置时发生错误: {e}", exc_info=True)
            return []

    def get_default_config_for_system(self) -> typing.Optional[BaseTTSConfig]:
        """
        为系统首次启动获取默认TTS配置
        
        专门用于系统首次启动时的场景，会自动检测系统语言并选择最合适的默认配置
        
        Returns:
            BaseTTSConfig: 系统默认配置
        """
        try:
            from utils.system import get_system_language
            system_language = get_system_language()
            logger.info(f"系统首次启动，检测到系统语言: {system_language}")

            default_config = self.get_default_config(user_language=system_language)

            if default_config:
                logger.info(
                    f"为系统首次启动选择默认TTS配置: {default_config.tts_type.value}:{default_config.character_name}")
                # 记录配置详情，方便调试
                logger.debug(f"默认配置详情: 语音类型={'中文' if default_config.is_chinese_voice else '非中文'}, "
                             f"模型完整性={'完整' if default_config.is_model_complete() else '未完整'}")
            else:
                logger.error("无法为系统首次启动选择默认TTS配置")

            return default_config

        except ImportError:
            logger.warning("无法导入系统语言检测模块，使用中文作为默认语言")
            return self.get_default_config(user_language='zh')
        except Exception as e:
            logger.error(f"为系统首次启动获取默认配置时发生错误: {e}", exc_info=True)
            return self.get_default_config(user_language='zh')


# 全局TTS注册表实例
tts_config_registry = TTSConfigRegistry()
