import importlib.util
import inspect
import re
from dataclasses import dataclass
from typing import Dict, Type, List, Literal, Optional

from voice_dialogue.utils.logger import logger
from .models import ASRInterface


@dataclass
class ASRRegistryTables:
    """ASR注册表系统，用于管理不同的ASR实现"""

    asr_classes: Dict[str, Type[ASRInterface]] = None

    def __post_init__(self):
        if self.asr_classes is None:
            self.asr_classes = {}

    def print(self, key: str = None) -> None:
        """打印已注册的ASR类"""
        logger.info("\nASR Registry Tables: \n")
        headers = ["register name", "class name", "class location", "supported languages"]

        if self.asr_classes and (key is None or "asr_classes" in key):
            logger.info(f"-----------    ** asr_classes **    --------------")
            metas = []
            for register_key, asr_class in self.asr_classes.items():
                class_file = inspect.getfile(asr_class)
                class_line = inspect.getsourcelines(asr_class)[1]
                # 简化路径显示
                pattern = r"^.+/VoiceDialogue/"
                class_file = re.sub(pattern, "VoiceDialogue/", class_file)

                # 获取支持的语言
                try:
                    supported_langs = asr_class.supported_langs
                    supported_langs_str = ', '.join(supported_langs) if supported_langs else 'unknown'
                except:
                    supported_langs_str = 'unknown'

                meta_data = [
                    register_key,
                    asr_class.__name__,
                    f"{class_file}:{class_line}",
                    supported_langs_str,
                ]
                metas.append(meta_data)

            metas.sort(key=lambda x: x[0])
            data = [headers] + metas
            col_widths = [max(len(str(item)) for item in col) for col in zip(*data)]

            for row in data:
                logger.info(
                    "| "
                    + " | ".join(str(item).ljust(width) for item, width in zip(row, col_widths))
                    + " |"
                )
        logger.info("\n")

    def register(self, register_table_key: str, key: str = None) -> callable:
        """装饰器，用于注册ASR类"""

        def decorator(target_class):
            if not hasattr(self, register_table_key):
                setattr(self, register_table_key, {})
                logger.debug(f"New ASR registry table added: {register_table_key}")

            registry = getattr(self, register_table_key)
            registry_key = key if key is not None else target_class.__name__

            if registry_key in registry:
                logger.debug(
                    f"Key {registry_key} already exists in {register_table_key}, re-register"
                )

            registry[registry_key] = target_class
            logger.info(f"Registered ASR class: {registry_key} -> {target_class.__name__}")
            return target_class

        return decorator


# 全局ASR注册表实例
asr_tables = ASRRegistryTables()


class ASRManager:
    """ASR管理器，负责管理和创建ASR实例"""

    def __init__(self):
        self._asr_instances: Dict[str, ASRInterface] = {}
        self._language_to_asr_mapping = {
            'zh': 'funasr',  # 中文优先使用FunASR
            'en': 'whisper',  # 英文优先使用Whisper
            # 'auto': 'whisper',  # 自动检测默认使用Whisper
        }

    def create_asr(self, language: Literal['auto', 'zh', 'en']) -> ASRInterface:
        """
        根据语言配置创建ASR实例
        
        Args:
            language: 语言类型
            
        Returns:
            ASRInterface: ASR实例
            
        Raises:
            ValueError: 如果ASR类型未注册或语言不支持
        """
        try:
            # 根据语言选择合适的ASR引擎
            asr_type = self._get_asr_type_for_language(language)

            if asr_type not in asr_tables.asr_classes:
                raise ValueError(f"ASR类型 '{asr_type}' 未注册")

            asr_class = asr_tables.asr_classes[asr_type]
            instance = asr_class()

            logger.info(f"成功创建ASR实例: {asr_type} for language: {language}")
            return instance

        except Exception as e:
            logger.error(f"创建ASR实例失败: {e}")
            raise

    def get_or_create_asr(self, language: Literal['auto', 'zh', 'en']) -> ASRInterface:
        """
        获取或创建ASR实例（单例模式）
        
        Args:
            language: 语言类型
            
        Returns:
            ASRInterface: ASR实例
        """
        asr_type = self._get_asr_type_for_language(language)
        instance_key = f"{asr_type}_{language}"

        if instance_key not in self._asr_instances:
            self._asr_instances[instance_key] = self.create_asr(language)

        return self._asr_instances[instance_key]

    def _get_asr_type_for_language(self, language: str) -> str:
        """根据语言获取对应的ASR类型"""
        asr_type = self._language_to_asr_mapping.get(language)
        if not asr_type:
            raise ValueError(f"不支持的语言类型: {language}")
        return asr_type

    def set_language_mapping(self, language: str, asr_type: str) -> None:
        """
        设置语言到ASR引擎的映射关系
        
        Args:
            language: 语言代码
            asr_type: ASR引擎类型
        """
        if asr_type not in asr_tables.asr_classes:
            raise ValueError(f"ASR类型 '{asr_type}' 未注册")

        self._language_to_asr_mapping[language] = asr_type
        logger.info(f"更新语言映射: {language} -> {asr_type}")

    def list_registered_asr(self) -> Dict[str, Type[ASRInterface]]:
        """列出所有已注册的ASR类型"""
        return asr_tables.asr_classes.copy()

    def is_asr_registered(self, asr_type: str) -> bool:
        """检查指定ASR类型是否已注册"""
        return asr_type in asr_tables.asr_classes

    def get_supported_languages(self) -> Dict[str, List[str]]:
        """
        获取所有已注册ASR引擎支持的语言列表
        
        Returns:
            Dict[str, List[str]]: ASR引擎名称到支持语言列表的映射
        """
        supported_languages = {}

        for asr_key, asr_class in asr_tables.asr_classes.items():
            try:
                supported_languages[asr_key] = asr_class.supported_langs
                # languages = asr_tables._get_asr_supported_languages(asr_key)
                # supported_languages[asr_key] = languages
            except Exception as e:
                logger.warning(f"获取ASR引擎 '{asr_key}' 支持的语言失败: {e}")
                supported_languages[asr_key] = ['unknown']

        return supported_languages

    def get_available_languages(self) -> List[str]:
        """
        获取当前可用的所有语言列表
        
        Returns:
            List[str]: 可用的语言代码列表
        """
        all_languages = set()
        supported_langs = self.get_supported_languages()

        for asr_key, languages in supported_langs.items():
            all_languages.update(languages)

        # 移除unknown标记
        all_languages.discard('unknown')
        return sorted(list(all_languages))

    def validate_language_support(self, language: str) -> bool:
        """
        验证指定语言是否被支持
        
        Args:
            language: 语言代码
            
        Returns:
            bool: 是否支持该语言
        """
        available_languages = self.get_available_languages()
        return language in available_languages

    def get_optimal_asr_for_language(self, language: str) -> Optional[str]:
        """
        为指定语言获取最优的ASR引擎
        
        Args:
            language: 语言代码
            
        Returns:
            Optional[str]: 最优的ASR引擎名称，如果没有支持的引擎则返回None
        """
        # 检查当前映射
        if language in self._language_to_asr_mapping:
            asr_type = self._language_to_asr_mapping[language]
            if self.is_asr_registered(asr_type):
                return asr_type

        # 查找支持该语言的ASR引擎
        supported_langs = self.get_supported_languages()
        for asr_key, languages in supported_langs.items():
            if language in languages:
                return asr_key

        return None

    def cleanup(self) -> None:
        """清理所有ASR实例"""
        logger.info("清理ASR实例...")
        self._asr_instances.clear()
        logger.info("ASR实例清理完成")

    def print_registry(self) -> None:
        """打印注册表信息"""
        asr_tables.print()

    def get_asr_statistics(self) -> Dict:
        """
        获取ASR管理器的统计信息
        
        Returns:
            Dict: 包含各种统计信息的字典
        """
        return {
            'registered_asr_count': len(asr_tables.asr_classes),
            'active_instances_count': len(self._asr_instances),
            'supported_languages': self.get_available_languages(),
            'language_mappings': self._language_to_asr_mapping.copy(),
            'registered_asr_types': list(asr_tables.asr_classes.keys())
        }


# 全局ASR管理器实例
asr_manager = ASRManager()


def register_all_asr():
    """自动发现并注册所有ASR实现"""
    import importlib
    from pathlib import Path

    # 获取models目录路径
    models_dir = Path(__file__).parent / "models"

    # 扫描models目录中的Python文件
    for py_file in models_dir.glob("*.py"):
        if py_file.name in ["__init__.py", "base.py"]:
            continue

        module_name = py_file.stem
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                module_name,
                py_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f"Successfully imported ASR module: {module_name}")
        except ImportError as e:
            logger.warning(f"Failed to import ASR module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error importing ASR module {module_name}: {e}")


# 在模块导入时自动注册所有ASR
register_all_asr()
