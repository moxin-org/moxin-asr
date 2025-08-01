# AECAudioStream

## 概述
AECAudioStream 是一个用于捕获系统音频输入并应用声学回声消除（AEC）过滤器的 Swift 库。它提供了一个便捷的接口，允许用户捕获音频数据、处理声学回声消除，并支持语音活动检测（VAD）功能。

## 功能特点
- 音频捕获：从系统音频输入设备捕获音频数据
- 声学回声消除（AEC）：通过内置过滤器消除回声
- 语音活动检测（VAD）：检测是否有语音活动
- 灵活的音频处理：支持自定义音频处理回调
- 线程安全的音频数据队列管理

## 系统要求
- macOS 操作系统
- Swift 5.0+

## 编译方法
使用以下命令编译生成动态库：
``` bash
swiftc -emit-library -o libAudioCapture.dylib AECAudioStream.swift
```
## 使用方法
### 初始化
``` swift
// 创建一个采样率为16000的音频流实例
let audioStream = AECAudioStream(sampleRate: 16000)
```
### 启动音频捕获
``` swift
// 启动音频流并启用回声消除
let audioBufferStream = try audioStream.startAudioStream(enableAEC: true)

// 异步处理捕获的音频数据
Task {
    for try await pcmBuffer in audioBufferStream {
        // 处理音频数据
        processAudioData(pcmBuffer)
    }
}
```
### 使用回调方式
``` swift
// 启动音频流并通过回调处理
try audioStream.startAudioStream(enableAEC: true) { buffer in
    // 通过回调处理音频数据
}
```
### 启用语音活动检测（VAD）
``` swift
// 启用VAD功能
try audioStream.toggleVoiceActivityDetection(enable: true)

// 设置VAD状态变化的回调
audioStream.voiceActivityHandler = { isVoiceDetected in
    if isVoiceDetected {
        print("检测到语音活动")
    } else {
        print("未检测到语音活动")
    }
}
```
### 停止音频捕获
``` swift
// 停止音频单元
try audioStream.stopAudioUnit()
```
## C 接口
库提供了以下 C 接口函数，方便从其他语言调用：
- `startRecord()`: 开始录音并将音频数据存入队列
- `stopRecord()`: 停止录音
- `getAudioData()`: 获取音频数据
- `freeAudioData()`: 释放音频数据缓冲区
- `isVoiceActive()`: 获取当前语音活动检测状态

### C 接口使用示例
``` c
// 开始录音
startRecord();

// 获取音频数据
int size;
uint8_t* audioData = getAudioData(&size);
if (audioData != NULL && size > 0) {
    // 处理音频数据
    processAudioData(audioData, size);
    
    // 处理完成后释放内存
    freeAudioData(audioData);
}

// 停止录音
stopRecord();
```
## 类和组件
### AECAudioStream
主要类，提供音频捕获和处理功能。
### AudioDataQueue
线程安全的音频数据队列，用于存储捕获的音频数据。
### AECAudioStreamError
定义可能抛出的错误类型。
## 注意事项
- 确保在使用完毕后调用 `stopAudioUnit()` 以释放资源
- 使用 VAD 功能时需要适当的权限
- 使用 C 接口获取音频数据后，必须调用 `freeAudioData()` 释放内存

## 许可证
[请在此处添加许可证信息]
