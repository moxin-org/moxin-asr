# API 服务指南

VoiceDialogue 支持通过 API 服务模式运行，启动一个 FastAPI Web 服务器，提供 HTTP 接口进行交互。

## 启动 API 服务

```bash
# 启动 API 服务器
python main.py --mode api
# 或使用 uv
uv run main.py --mode api

# 指定不同端口和启用热重载
python main.py --mode api --port 9000 --reload
```

## API 服务特性

- **API 文档地址**: 启动服务后，可在 `http://localhost:8000/docs` 查看交互式 API 文档 (Swagger UI)。
- **TTS 模型管理**: 支持通过 API 查看、加载、删除 TTS 模型。
- **实时模型状态监控**: 提供接口查询当前加载的模型和系统状态。
- **RESTful API 设计**: 采用标准的 RESTful 设计，方便与其他应用集成。

## 主要接口

### TTS模型管理

* `GET /api/v1/tts/models` - 获取所有可用的TTS模型列表
* `POST /api/v1/tts/models/load` - 加载指定的TTS模型
* `GET /api/v1/tts/models/{model_id}/status` - 查看模型下载和加载状态
* `DELETE /api/v1/tts/models/{model_id}` - 删除已下载的模型

### 语音识别管理

* `GET /api/v1/asr/languages` - 获取支持的识别语言列表
* `POST /api/v1/asr/instance/create` - 创建指定语言的ASR实例

### 系统控制

* `GET /api/v1/system/status` - 获取系统整体状态
* `POST /api/v1/system/start` - 启动语音对话系统
* `POST /api/v1/system/stop` - 停止语音对话系统
* `POST /api/v1/system/restart` - 重启语音对话系统

### 实时通信

* `WebSocket /api/v1/ws` - WebSocket连接，接收实时系统消息

更多详细信息请参考启动服务后的在线API文档。 