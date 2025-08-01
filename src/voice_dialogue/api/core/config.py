from typing import Dict, Any

from voice_dialogue.tts import tts_config_registry
from voice_dialogue.utils.logger import logger


class TTSConfigInitializer:
    """TTS配置初始化器"""

    @staticmethod
    def initialize() -> Dict[str, Any]:
        """初始化TTS配置"""
        result = {
            "tts_configs_loaded": False,
            "tts_config_count": 0,
            "tts_config_errors": []
        }

        try:
            config_count = len(tts_config_registry.get_all_configs())

            result.update({
                "tts_configs_loaded": True,
                "tts_config_count": config_count
            })

            logger.info(f"已加载 {config_count} 个TTS配置")

        except ImportError as e:
            error_msg = f"TTS模块导入失败: {e}"
            logger.error(error_msg)
            result["tts_config_errors"].append(error_msg)

        except Exception as e:
            error_msg = f"TTS配置加载失败: {e}"
            logger.error(error_msg, exc_info=True)
            result["tts_config_errors"].append(error_msg)

        return result


class AppConfig:
    """应用配置类"""

    def __init__(self):
        self.title = "VoiceDialogue API"
        self.version = "1.0.0"
        self.description = self._get_description()
        self.docs_url = "/docs"
        self.redoc_url = "/redoc"

    def _get_description(self) -> str:
        return """
        # VoiceDialogue - 智能语音对话系统 API

        一个基于人工智能的完整语音对话系统，集成了语音识别(ASR)、大语言模型(LLM)和文本转语音(TTS)技术，提供端到端的语音交互体验。

        ## 🚀 核心功能

        ### 🎤 语音识别 (ASR)
        * **多语言支持**: 中文(FunASR)、英文及其他语言(Whisper)
        * **智能引擎切换**: 根据语言自动选择最优识别引擎
        * **实时语音转文本**: 低延迟的语音识别处理
        * **动态语言切换**: 运行时创建和切换不同语言的ASR实例

        ### 🤖 智能对话
        * **大语言模型集成**: 基于Qwen等先进模型
        * **上下文理解**: 支持多轮对话和上下文记忆
        * **自定义系统提示**: 可配置AI助手的行为和角色，支持用户自定义

        ### 🎭 高质量语音合成 (TTS)
        * **多角色支持**: 集成多种高质量TTS引擎，支持丰富的中英文角色
        * **智能引擎选择**: 根据内容语言自动选择最适合的TTS引擎
        * **动态角色管理**: 运行时加载、切换和管理语音角色

        ### ⚡ 实时通信
        * **WebSocket连接**: 支持实时语音消息推送
        * **状态监控**: 实时监控系统和模型状态
        * **会话管理**: 智能的会话ID管理和消息路由

        ### 🔧 系统管理与设置
        * **服务生命周期**: 完整的系统启动、停止、重启控制
        * **音频捕获**: 高质量的音频输入处理和回声消除
        * **状态监控**: 详细的服务状态和性能指标
        * **用户配置**: 支持用户通过API自定义和持久化应用设置

        ## 📋 主要API端点

        ### 设置管理 (Settings)
        * `GET /api/v1/settings/prompts` - 获取当前生效的系统Prompt
        * `POST /api/v1/settings/prompts` - 更新并保存用户自定义的Prompt
        * `DELETE /api/v1/settings/prompts` - 重置Prompt为系统默认值
        * `GET /api/v1/settings/prompts/default` - 获取系统默认的Prompt

        ### TTS模型管理 (TTS)
        * `GET /api/v1/tts/models` - 获取所有可用的TTS模型列表
        * `POST /api/v1/tts/models/load` - 加载指定的TTS模型
        * `GET /api/v1/tts/models/{model_id}/status` - 查看模型下载和加载状态
        * `DELETE /api/v1/tts/models/{model_id}` - 删除已下载的模型

        ### 语音识别管理 (ASR)
        * `GET /api/v1/asr/languages` - 获取支持的识别语言列表
        * `POST /api/v1/asr/instance/create` - 创建指定语言的ASR实例

        ### 系统控制 (System)
        * `GET /api/v1/system/status` - 获取系统整体状态
        * `POST /api/v1/system/start` - 启动语音对话系统
        * `POST /api/v1/system/stop` - 停止语音对话系统  
        * `POST /api/v1/system/restart` - 重启语音对话系统

        ### 实时通信 (WebSocket)
        * `WebSocket /api/v1/ws` - WebSocket连接，接收实时系统消息

        ## 🛠️ 技术特性

        * **异步处理**: 基于FastAPI的高性能异步架构
        * **后台任务**: 模型下载和加载在后台执行，不阻塞API响应
        * **可配置性**: 支持用户通过API和配置文件自定义核心行为
        * **持久化存储**: 用户设置可被持久化，重启应用后依然生效
        * **内存缓存**: 缓存常用配置，减少磁盘I/O，提升性能
        * **API文档**: 自动生成的交互式API文档(Swagger & ReDoc)

        ## 💡 使用场景

        * **智能客服**: 语音客服机器人和自动问答系统
        * **语音助手**: 个人或企业级语音助手应用
        * **内容创作**: 语音内容生成和多角色配音
        * **教育培训**: 语音交互式学习和培训系统
        * **无障碍应用**: 视力障碍用户的语音交互界面
        """

    def get_cors_config(self) -> dict:
        """获取CORS配置"""
        return {
            "allow_origins": ["*"],  # 生产环境中应该设置具体的域名
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
