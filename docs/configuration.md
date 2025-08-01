# 配置指南

本文档介绍如何配置 VoiceDialogue 系统。

## 启动参数

通过 `main.py` 的命令行参数可以方便地进行配置：

| 参数 | 缩写 | 可选值 | 默认值 | 描述 |
|---|---|---|---|---|
| `--mode` | `-m` | `cli`, `api` | `cli` | 设置运行模式 |
| `--language`| `-l` | `zh`, `en` | `zh` | (CLI模式) 设置用户语言 |
| `--speaker` | `-s` | (动态获取) | `沈逸` | (CLI模式) 设置TTS语音角色 |
| `--host` | | IP地址 | `0.0.0.0` | (API模式) 服务器主机 |
| `--port` | `-p` | 端口号 | `8000` | (API模式) 服务器端口 |
| `--reload`| | 无 | `False` | (API模式) 启用热重载 |

**支持的说话人角色**（动态加载）:

- **中文角色**：`罗翔`, `马保国`, `沈逸`, `杨幂`, `周杰伦`, `马云`
- **英文角色**：`Heart`, `Bella`, `Nicole`

## 高级配置

### 大语言模型 (LLM)

- **模型路径和参数**: LLM 的模型和推理参数目前在代码中硬编码，方便快速启动。
- **文件位置**: `src/VoiceDialogue/services/text/generator.py`
- **自定义**: 你可以修改 `LLMResponseGenerator` 类中的配置。

### 语音识别 (ASR)

- **引擎自动选择**: 系统会根据 `--language` 参数自动选择最合适的 ASR 引擎。
- **模型配置**: ASR 模型的具体配置位于 `src/VoiceDialogue/services/speech/recognizers/manager.py`。

### 系统提示词 (System Prompt)

- **功能**: 定义 AI 角色的行为和说话风格。
- **文件位置**: `src/VoiceDialogue/services/text/generator.py`
- **自定义**: 你可以修改系统提示词变量的值。

## 构建完整应用

项目提供了完整的构建脚本，可以一键构建包含Python后端和Electron前端的完整应用：

1. 首先，激活当前 Python 环境

   ```bash
   source .venv/bin/activate
   # 或使用 conda
   conda activate voicedialogue
   ```

2. 使用构建脚本

   ```bash
   # 使用构建脚本（推荐）
   bash scripts/build.sh

   # 或分别构建
   bash scripts/build-python.sh  # 构建Python后端
   bash scripts/build-electron.sh # 构建Electron前端

   # 清理构建产物
   bash scripts/clean.sh
   ``` 