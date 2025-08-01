# VoiceDialogue 安装指南

本文档提供 VoiceDialogue 智能语音对话系统的详细安装说明。

## 系统要求

在开始安装之前，请确保您的系统满足以下要求：

- **操作系统**: macOS 14+ (推荐)
- **Python 版本**: 3.9 或更高版本
- **内存要求**: 至少 16GB RAM (推荐 32GB 用于大模型)
- **存储空间**: 至少 20GB 可用空间 (用于模型文件)

## 安装步骤

### 1. 克隆项目

```bash
git clone https://huggingface.co/MoYoYoTech/VoiceDialogue
cd VoiceDialogue
```

### 2. 创建并激活虚拟环境

建议使用虚拟环境来避免依赖冲突：

```bash
# 使用 uv (推荐)
pip install uv
uv venv
source .venv/bin/activate

# 或使用 conda
conda create -n voicedialogue python=3.11
conda activate voicedialogue

# 或使用 venv
python -m venv voicedialogue
source voicedialogue/bin/activate
```

### 3. 安装项目依赖

```bash
# 使用 uv (推荐)
WHISPER_COREML=1 CMAKE_ARGS="-DGGML_METAL=on" uv sync

# 或使用 pip
WHISPER_COREML=1 CMAKE_ARGS="-DGGML_METAL=on" pip install -r requirements.txt
```

### 4. 安装音频处理工具

```bash
# macOS
brew install ffmpeg
```

### 5. 安装额外依赖

```bash
# 安装 kokoro-onnx
uv pip install kokoro-onnx
# 或
pip install kokoro-onnx

# 重新安装指定版本的 numpy
uv pip install numpy==1.26.4
# 或
pip install numpy==1.26.4
```

## 验证安装

安装完成后，可以通过以下命令验证安装是否成功：

```bash
# 查看帮助信息
python main.py --help

# 启动系统（默认使用中文，沈逸角色）
python main.py
```

如果看到 "服务启动成功" 提示，说明安装成功。

## 故障排除

### 1. 模型下载失败
- **问题**: 网络连接超时或模型下载失败。
- **解决方案**: 设置 Hugging Face 镜像。
```bash
export HF_ENDPOINT=https://hf-mirror.com
pip install -U huggingface_hub
```

### 2. 音频设备问题
- **问题**: 找不到音频设备或权限被拒绝。
- **macOS 解决方案**: 系统设置 → 隐私与安全性 → 麦克风 → 启用你的终端应用 (如 iTerm, Terminal)。

### 3. 内存不足错误 (OOM)
- **问题**: `CUDA out of memory` 或 RAM 不足。
- **解决方案**: LLM 是主要的内存消耗者。你可以通过修改 `src/VoiceDialogue/services/text/generator.py` 来降低资源消耗：
    - **更换模型**: 将模型路径指向一个更小的模型（如 7B Q4 量化模型）。
    - **减少批处理大小**: 减小模型参数中的 `n_batch` 值（如 `256`）。
    - **减少上下文长度**: 减小 `n_ctx` 的值（如 `1024`）。

### 4. 依赖包冲突
- **问题**: 包版本冲突或导入错误。
- **解决方案**: 强烈建议在虚拟环境中安装。如果遇到问题，尝试重建虚拟环境。
```bash
# 使用 conda
conda deactivate
conda env remove -n voicedialogue

# 使用 uv
rm -rf .venv
uv venv
```

### 5. FFmpeg 相关错误
- **问题**: 音频处理失败或编解码错误。
- **解决方案**: 确保正确安装 FFmpeg：
```bash
# 检查 FFmpeg 安装
ffmpeg -version

# 重新安装 FFmpeg
# macOS
brew reinstall ffmpeg
```

### 6. Python 版本兼容性
- **问题**: Python 版本过低导致的兼容性问题。
- **解决方案**: 确保使用 Python 3.11+ 版本：
```bash
python --version
# 如果版本过低，请升级或使用虚拟环境
```

## 下一步

安装完成后，您可以：

1. [查看使用指南](../README.md#🖥️-应用模式) 了解如何使用系统
2. [查看配置选项](../README.md#⚙️-配置选项) 了解如何自定义配置
3. [查看系统架构](../README.md#🔧-系统架构) 了解系统工作原理

如果遇到其他问题，请查看 [完整故障排除指南](../README.md#🛠️-故障排除) 或提交 Issue。 