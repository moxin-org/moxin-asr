import os
import sys
from pathlib import Path

# 项目根目录
HERE = Path(__file__).parent
_project_root = getattr(sys, '_MEIPASS', HERE.parent.parent.parent.as_posix())
PROJECT_ROOT = Path(_project_root)

# 资源路径 - 统一到assets目录
ASSETS_PATH = PROJECT_ROOT / "assets"
MODELS_PATH = ASSETS_PATH / "models"

# 具体模型类型路径
ASR_MODELS_PATH = MODELS_PATH / "asr"
TTS_MODELS_PATH = MODELS_PATH / "tts"
LLM_MODELS_PATH = MODELS_PATH / "llm"

# 第三方库路径
THIRD_PARTY_PATH = PROJECT_ROOT / "third_party"

# 其他资源路径
LIBRARIES_PATH = ASSETS_PATH / "libraries"
AUDIO_RESOURCES_PATH = ASSETS_PATH / "audio"

# 前端静态资源路径
FRONTEND_ASSETS_PATH = ASSETS_PATH / "www"


# 用户数据路径 - 根据操作系统选择合适的目录
def get_app_data_path() -> Path:
    """获取应用数据存储路径"""
    app_name = "Voice Dialogue"

    if sys.platform == "darwin":  # macOS
        base_path = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":  # Windows
        base_path = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:  # Linux and others
        base_path = Path.home() / ".config"

    return base_path / app_name


APP_DATA_PATH = get_app_data_path()
if not APP_DATA_PATH.exists():
    APP_DATA_PATH.mkdir(parents=True, exist_ok=True)
USER_PROMPTS_PATH = APP_DATA_PATH / "user_prompts.json"


def load_third_party():
    # 添加第三方库到 Python 路径
    if THIRD_PARTY_PATH.exists() and str(THIRD_PARTY_PATH) not in sys.path:
        sys.path.insert(0, str(THIRD_PARTY_PATH))
