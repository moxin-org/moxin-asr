# 故障排除与性能优化

## 🛠️ 故障排除

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
- **Linux 解决方案**: `sudo usermod -a -G audio $USER`，然后重新登录。

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
deactivate
rm -rf .venv
```

### 5. 说话人角色不存在
- **问题**: 指定的说话人不在支持列表中。
- **解决方案**: 使用 `python main.py --help` 查看所有可用的说话人角色。

### 6. FFmpeg 相关错误
- **问题**: 音频处理失败或编解码错误。
- **解决方案**: 确保正确安装 FFmpeg：
```bash
# 检查 FFmpeg 安装
ffmpeg -version

# 重新安装 FFmpeg
# macOS
brew reinstall ffmpeg

```

### 7. Python 版本兼容性
- **问题**: Python 版本过低导致的兼容性问题。
- **解决方案**: 确保使用 Python 3.9+ 版本：
```bash
python --version
# 如果版本过低，请升级或使用虚拟环境
```

### 8. 桌面应用相关问题
- **问题**: Electron 应用启动失败或功能异常。
- **解决方案**: 
  - 确保 Node.js 版本 >= 16
  - 重新安装依赖：`cd electron-app && npm install`
  - 检查 Python 后端是否正常运行

### 9. 构建打包问题
- **问题**: 使用构建脚本失败。
- **解决方案**: 
  - 确保有执行权限：`chmod +x scripts/*.sh`
  - 检查所有依赖是否安装完成
  - 查看具体错误日志进行调试

## 📊 性能优化建议

### 硬件优化
- **内存**: 推荐 32GB RAM 以获得最佳性能
- **存储**: 使用 SSD 硬盘可显著提升模型加载速度
- **CPU**: 多核处理器有助于多线程处理

### 软件优化
- **模型选择**: 根据硬件配置选择合适大小的模型
- **批处理优化**: 调整 LLM 的 `n_batch` 参数
- **音频缓冲**: 根据延迟要求调整音频缓冲区大小 