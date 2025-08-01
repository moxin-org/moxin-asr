---
title: VoiceDialogue - 智能语音对话系统
license: mit
language:
  - zh
  - en
pipeline_tag: text-to-speech
tags:
  - voice-dialogue
  - speech-recognition
  - text-to-speech
  - large-language-model
  - asr
  - tts
  - llm
  - chinese
  - english
  - real-time
library_name: transformers
---

# VoiceDialogue - 智能语音对话系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)
![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)

一个集成了语音识别(ASR)、大语言模型(LLM)和文本转语音(TTS)的实时语音对话系统

[快速开始](#-快速开始) • [文档导航](#-文档导航) • [贡献指南](docs/contributing.md)

</div>

## 🎯 项目简介

VoiceDialogue 是一个基于 Python 的完整语音对话系统，实现了端到端的语音交互体验。系统采用模块化设计，具备实时、高精度、多角色的特点。

- 🎤 **实时语音识别**: 高精度中英文语音转录
- 🤖 **智能对话生成**: 集成 Qwen2.5 等大语言模型
- 🔊 **高质量语音合成**: 支持多角色、多风格的语音输出
- 🌐 **Web API 服务**: 提供 HTTP 接口，方便集成
- ⚡ **低延迟处理**: 优化的音频流处理管道

> 想要了解更多？请查看 [功能特性详解](docs/features.md)。

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://huggingface.co/MoYoYoTech/VoiceDialogue
cd VoiceDialogue

# 安装依赖 (推荐使用 uv)
pip install uv
uv venv
source .venv/bin/activate

WHISPER_COREML=1 CMAKE_ARGS="-DGGML_METAL=on" uv sync

# 安装额外的依赖
## 1. 安装 kokoro-onnx
uv pip install kokoro-onnx
## 2. 重新安装指定版本的 numpy
uv pip install numpy==1.26.4
```

> 📖 需要更详细的步骤？请查阅 [安装指南](docs/installation.md)，其中包含系统要求和常见问题。

### 2. 运行

#### 命令行模式 (CLI)

```bash
# 启动语音对话 (默认中文)
python main.py

# 启动并指定语言和角色
python main.py --language en --speaker Heart
```

#### API 服务模式

```bash
# 启动 API 服务器
python main.py --mode api
```
> 详细使用方法请参考 [配置指南](docs/configuration.md) 和 [API 服务指南](docs/api-guide.md)。

## 📚 文档导航

- 📖 **[安装指南](docs/installation.md)**: 详细的安装步骤和系统要求。
- ⚙️ **[配置指南](docs/configuration.md)**: 如何配置系统参数和高级选项。
- 🎭 **[功能特性](docs/features.md)**: 深入了解项目的所有功能。
- 🌐 **[API 指南](docs/api-guide.md)**: 如何使用和集成 API 服务。
- 🏗️ **[系统架构](docs/architecture.md)**: 了解系统的内部工作原理。
- 📁 **[项目结构](docs/project-structure.md)**: 浏览项目代码和文件组织。
- 🛠️ **[故障排除](docs/troubleshooting.md)**: 常见问题和解决方案。
- 🤝 **[贡献指南](docs/contributing.md)**: 如何为项目做出贡献。

## 📄 许可证

本项目采用 MIT 许可证开源。

## 🙏 致谢

如果这个项目对您有帮助，请给我们一个 ⭐️!