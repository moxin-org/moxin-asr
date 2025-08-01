import importlib.util
import inspect
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Type

from voice_dialogue.utils.logger import logger
from .models.base import BaseTTSConfig
from .runtime.interface import TTSInterface


@dataclass
class TTSRegistryTables:
    """TTS注册表系统，用于管理不同的TTS实现"""

    tts_classes: Dict[str, Type[TTSInterface]] = None

    def __post_init__(self):
        if self.tts_classes is None:
            self.tts_classes = {}

    def print(self, key: str = None) -> None:
        """打印已注册的TTS类"""
        logger.info("\nTTS Registry Tables: \n")
        headers = ["register name", "class name", "class location"]

        if self.tts_classes and (key is None or "tts_classes" in key):
            logger.info(f"-----------    ** tts_classes **    --------------")
            metas = []
            for register_key, tts_class in self.tts_classes.items():
                class_file = inspect.getfile(tts_class)
                class_line = inspect.getsourcelines(tts_class)[1]
                # 简化路径显示
                pattern = r"^.+/VoiceDialogue/"
                class_file = re.sub(pattern, "VoiceDialogue/", class_file)
                meta_data = [
                    register_key,
                    tts_class.__name__,
                    f"{class_file}:{class_line}",
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
        """装饰器，用于注册TTS类"""

        def decorator(target_class):
            if not hasattr(self, register_table_key):
                setattr(self, register_table_key, {})
                logger.debug(f"New TTS registry table added: {register_table_key}")

            registry = getattr(self, register_table_key)
            registry_key = key if key is not None else target_class.__name__

            if registry_key in registry:
                logger.debug(
                    f"Key {registry_key} already exists in {register_table_key}, re-register"
                )

            registry[registry_key] = target_class
            logger.info(f"Registered TTS class: {registry_key} -> {target_class.__name__}")
            return target_class

        return decorator


# 全局TTS注册表实例
tts_tables = TTSRegistryTables()


class TTSManager:
    """TTS管理器，负责管理和创建TTS实例"""

    def __init__(self):
        self._tts_instances: Dict[str, TTSInterface] = {}

    def create_tts(self, config: BaseTTSConfig) -> TTSInterface:
        """
        根据配置创建TTS实例
        
        Args:
            config: TTS配置对象
            
        Returns:
            TTSInterface: TTS实例
            
        Raises:
            ValueError: 如果TTS类型未注册
        """
        tts_type = config.tts_type.value

        if tts_type not in tts_tables.tts_classes:
            raise ValueError(f"未注册的TTS类型: {tts_type}. 可用类型: {list(tts_tables.tts_classes.keys())}")

        tts_class = tts_tables.tts_classes[tts_type]
        return tts_class(config)

    def get_or_create_tts(self, config: BaseTTSConfig) -> TTSInterface:
        """
        获取或创建TTS实例（单例模式）
        
        Args:
            config: TTS配置对象
            
        Returns:
            TTSInterface: TTS实例
        """
        instance_key = f"{config.tts_type.value}:{config.character_name}"

        if instance_key not in self._tts_instances:
            self._tts_instances[instance_key] = self.create_tts(config)

        return self._tts_instances[instance_key]

    def list_registered_tts(self) -> Dict[str, Type[TTSInterface]]:
        """列出所有已注册的TTS类"""
        return tts_tables.tts_classes.copy()

    def is_tts_registered(self, tts_type: str) -> bool:
        """检查指定TTS类型是否已注册"""
        return tts_type in tts_tables.tts_classes

    def print_registry(self):
        """打印注册表信息"""
        tts_tables.print()


# 全局TTS管理器实例
tts_manager = TTSManager()


def register_all_tts():
    """自动发现并注册runtime目录中的所有TTS实现"""

    # 获取runtime目录路径
    runtime_dir = Path(__file__).parent / "runtime"

    # 扫描runtime目录中的Python文件
    for py_file in runtime_dir.glob("*.py"):
        if py_file.name in ["__init__.py", "interface.py"]:
            continue

        module_name = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(
                module_name,
                py_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f"Successfully imported TTS module: {module_name}")
        except ImportError as e:
            logger.warning(f"Failed to import TTS module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error importing TTS module {module_name}: {e}")


# 在模块导入时自动注册所有TTS
register_all_tts()
