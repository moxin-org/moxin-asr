# 项目结构

```text
VoiceDialogue/
├── assets/                           # 资源文件
│   ├── models/                       # ASR, LLM, TTS 模型文件
│   └── ...                           # 其他资源 (音频, 库)
├── docs/                             # 项目文档
├── electron-app/                     # Electron 桌面应用 (打包后的)
├── frontend/                         # 前端源代码 (Vue.js)
│   ├── src/
│   │   ├── App.vue                   # 根组件
│   │   ├── main.ts                   # Vue 应用入口
│   │   ├── router.ts                 # 路由配置
│   │   ├── stores/                   # Pinia 状态管理
│   │   └── views/                    # 页面视图
│   └── vite.config.ts                # Vite 配置文件
├── scripts/                          # 构建和部署脚本
├── src/
│   └── voice_dialogue/                # Python 后端主要源代码
│       ├── api/                      # Web API 模块 (FastAPI)
│       │   ├── routes/               # API 路由定义
│       │   ├── schemas/              # Pydantic 数据模型
│       │   └── server.py             # Uvicorn 服务器启动
│       ├── asr/                      # 语音识别 (ASR) 子系统
│       │   ├── manager.py            # ASR 模型统一管理器
│       │   └── models/               # 具体 ASR 模型实现 (Funasr, Whisper)
│       ├── audio/                    # 音频 I/O 子系统
│       │   ├── capture/              # 音频捕获 (带回声消除)
│       │   └── player.py             # 音频播放
│       ├── config/                   # 配置管理
│       ├── core/                     # 核心应用框架 (启动器, 状态管理等)
│       ├── llm/                      # 大语言模型 (LLM) 子系统
│       ├── services/                 # 业务流程编排服务
│       ├── tts/                      # 文本转语音 (TTS) 子系统
│       │   ├── manager.py            # TTS 模型统一管理器
│       │   └── models/               # 具体 TTS 模型实现 (Kokoro, Moyo-TTS)
│       └── utils/                    # 通用工具函数
├── third_party/                      # 第三方库代码
├── main.py                           # 项目启动入口
├── pyproject.toml                    # Python 项目配置文件 (uv)
├── roadmap.md                        # [新] 项目路线图
└── README.md                         # 项目说明文档
```
