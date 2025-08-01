//
//  AECAudioStream.swift
//  Translator
//
//  Created by COldish on 5/16/25.
//

import CoreAudio
import Foundation
import AVFAudio
import OSLog


class AudioDataPacket {
    let audioData: Data
    let isVoiceActive: Bool
    
    init(audioData: Data, isVoiceActive: Bool) {
        self.audioData = audioData
        self.isVoiceActive = isVoiceActive
    }
}

class AudioDataQueue {
    private var queue = [AudioDataPacket]()
    private let lock = NSLock()
    private let capacity: Int
    
    init(capacity: Int = 100) {
        self.capacity = capacity
    }
    
    func push(data: Data, isVoiceActive: Bool) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        
        if queue.count < capacity {
            queue.append(AudioDataPacket(audioData: data, isVoiceActive: isVoiceActive))
            return true
        }
        return false
    }
    
    func pop() -> AudioDataPacket? {
        lock.lock()
        defer { lock.unlock() }
        
        if !queue.isEmpty {
            return queue.removeFirst()
        }
        return nil
    }
    
    var isEmpty: Bool {
        lock.lock()
        defer { lock.unlock() }
        return queue.isEmpty
    }
}

/**
 The `AECAudioStreamError` enumeration defines errors that can be thrown by the `AECAudioStream` class.
 
 - Version: 1.0
 */
public enum AECAudioStreamError: Error{
    /// An error that indicates an `OSStatus` error occurred.
    case osStatusError(status: OSStatus)
}

/**
 The `AECAudioStream` class provides an interface for capturing audio data from the system's audio input and applying an acoustic echo cancellation (AEC) filter to it. The class also allows you to play audio data through the audio unit's speaker using a renderer callback(testing feature).
 
 To use this class, create an instance with the desired sample rate and enable the renderer callback if needed. Then call the `startAudioStream` method to start capturing audio data and applying the AEC filter.
 
 - Version: 1.0
 */
public class AECAudioStream {
    
    private(set) var audioUnit: AudioUnit?
    
    private(set) var graph: AUGraph?
    
    private(set) var streamBasicDescription: AudioStreamBasicDescription
    
    private let logger = Logger(subsystem: "com.0x67.echo-cancellation.AECAudioUnit", category: "AECAudioStream")
    
    private(set) var sampleRate: Float64
    
    private(set) var streamFormat: AVAudioFormat
    
    private(set) var enableAutomaticEchoCancellation: Bool = false
    
    /// Provide AudioBufferList data in this closure to have speaker in this audio unit play you audio, only works if ``enableRendererCallback`` is set to `true`
    public var rendererClosure: ((UnsafeMutablePointer<AudioBufferList>, UInt32) -> Void)?
    
    /// A Boolean value that indicates whether to enable built-in audio unit's renderrer callback
    public var enableRendererCallback: Bool = false
    
    private(set) var capturedFrameHandler: ((AVAudioPCMBuffer) -> Void)?
    
    // 用于VAD的属性
    private var deviceID: AudioObjectID = 0
    private(set) var isVoiceActivityDetectionEnabled: Bool = false
    private(set) var isVoiceDetected: Bool = false
    
    // VAD状态变化的回调
    public var voiceActivityHandler: ((Bool) -> Void)?

    public func updateVoiceDetectionState(_ detected: Bool) {
        self.isVoiceDetected = detected
        // 调用用户提供的处理程序
        self.voiceActivityHandler?(detected)
        // DispatchQueue.main.async {
        // }
    }

    /**
     Initializes an instance of an audio stream object with the specified sample rate.
     
     - Parameter sampleRate: The sample rate of the audio stream.
     
     - Parameter enableRendererCallback: A Boolean value that indicates whether to enable a renderer callback, if enabled data provided in `rendererClosure` will be send to speaker
     
     - Parameter rendererClosure: A closure that takes an `UnsafeMutablePointer<AudioBufferList>` and a `UInt32` as input.
     
     - Returns: None.
     */
    public init(sampleRate: Float64,
                enableRendererCallback: Bool = false,
                rendererClosure: ((UnsafeMutablePointer<AudioBufferList>, UInt32) -> Void)? = nil) {
        self.sampleRate = sampleRate
        self.streamBasicDescription = Self.canonicalStreamDescription(sampleRate: sampleRate)
        self.streamFormat = AVAudioFormat(streamDescription: &self.streamBasicDescription)!
        self.enableRendererCallback = enableRendererCallback
        self.rendererClosure = rendererClosure
    }
    
    /**
     Starts an audio stream filter that captures audio data from the system's audio input and applies an acoustic echo cancellation (AEC) filter to it.
     
     - Parameter enableAEC: A Boolean value that indicates whether to enable the AEC filter.
     
     - Parameter enableRendererCallback: A Boolean value that indicates whether to enable a renderer callback, if enabled data provided in `rendererClosure` will be send to speaker
     
     - Parameter rendererClosure: A closure that takes an `UnsafeMutablePointer<AudioBufferList>` and a `UInt32` as input.
     
     - Returns: An `AsyncThrowingStream` that yields `AVAudioPCMBuffer` objects containing the captured audio data.
     
     - Throws: An error if there was a problem creating or configuring the audio unit, or if the AEC filter could not be enabled.
     */
    public func startAudioStream(enableAEC: Bool,
                                 enableRendererCallback: Bool = false,
                                 rendererClosure: ((UnsafeMutablePointer<AudioBufferList>, UInt32) -> Void)? = nil) -> AsyncThrowingStream<AVAudioPCMBuffer, Error> {
        AsyncThrowingStream<AVAudioPCMBuffer, Error> { continuation in
            do {
                
                self.enableRendererCallback = enableRendererCallback
                self.rendererClosure = rendererClosure
                self.capturedFrameHandler = {continuation.yield($0)}
                
                try createAUGraphForAudioUnit()
                try configureAudioUnit()
                try toggleAudioCancellation(enable: enableAEC)
                try startGraph()
                try startAudioUnit()
            } catch {
                continuation.finish(throwing: error)
            }
        }
    }
    
    /**
     Starts an audio stream  that captures audio data from the system's audio input and applies an acoustic echo cancellation (AEC) filter to it.
     
     - Parameter enableAEC: A Boolean value that indicates whether to enable the AEC filter.
     
     - Parameter audioBufferHandler: A closure that takes an `AVAudioPCMBuffer` object containing the captured audio data.
     
     - Returns: None.
     
     - Throws: An error if there was a problem creating or configuring the audio unit, or if the AEC filter could not be enabled.
     */
    public func startAudioStream(enableAEC: Bool,
                                 enableRendererCallback: Bool = false,
                                 rendererClosure: ((UnsafeMutablePointer<AudioBufferList>, UInt32) -> Void)? = nil) throws {
        self.enableRendererCallback = enableRendererCallback
        try createAUGraphForAudioUnit()
        try configureAudioUnit()
        try toggleAudioCancellation(enable: enableAEC)
        try startGraph()
        try startAudioUnit()
        self.rendererClosure = rendererClosure
    }
    
    /**
     Stops the audio unit and disposes of the audio graph.
     
     - Throws: An `AECAudioStreamError` if any of the operations fail.
     
     - Returns: None.
     */
    public func stopAudioUnit() throws {
        var status = AUGraphStop(graph!)
        guard status == noErr else {
            logger.error("AUGraphStop failed")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        status = AudioUnitUninitialize(audioUnit!)
        guard status == noErr else {
            logger.error("AudioUnitUninitialize failed")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        status = DisposeAUGraph(graph!)
        guard status == noErr else {
            logger.error("DisposeAUGraph failed")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        // 如果启用了VAD，需要移除监听器
        if isVoiceActivityDetectionEnabled {
            var vadStateAddress = AudioObjectPropertyAddress(
                mSelector: kAudioDevicePropertyVoiceActivityDetectionState,
                mScope: kAudioDevicePropertyScopeInput,
                mElement: kAudioObjectPropertyElementMain
            )
            
            AudioObjectRemovePropertyListener(
                deviceID,
                &vadStateAddress,
                vadStateListenerCallback,
                Unmanaged.passUnretained(self).toOpaque()
            )
        }        
    }

    private func toggleAudioCancellation(enable: Bool) throws {
        guard let audioUnit = audioUnit else {return}
        self.enableAutomaticEchoCancellation = enable
        // 0 means feature is enabled, which includes built-in echo cancellation. When the property is set to true, the voice processing feature is bypassed and no echo cancellation is performed.
        var bypassVoiceProcessing: UInt32 = self.enableAutomaticEchoCancellation ? 0 : 1
        var status = AudioUnitSetProperty(audioUnit, kAUVoiceIOProperty_BypassVoiceProcessing, kAudioUnitScope_Global, 0, &bypassVoiceProcessing, UInt32(MemoryLayout.size(ofValue: bypassVoiceProcessing)))
        guard status == noErr else {
            logger.error("Error in [AudioUnitSetProperty|kAUVoiceIOProperty_BypassVoiceProcessing|kAudioUnitScope_Global]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        var agcVoiceProcessing: UInt32 = self.enableAutomaticEchoCancellation ? 0 : 1
        status = AudioUnitSetProperty(audioUnit, kAUVoiceIOProperty_VoiceProcessingEnableAGC, kAudioUnitScope_Global, 0, &agcVoiceProcessing,UInt32(MemoryLayout.size(ofValue: agcVoiceProcessing)))
        guard status == noErr else {
            logger.error("Error in [AudioUnitSetProperty|kAUVoiceIOProperty_VoiceProcessingEnableAGC|kAudioUnitScope_Global]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
    }
    
    /**
     启用或禁用语音活动检测(VAD)功能
     
     - Parameter enable: 是否启用VAD
     - Returns: 无
     - Throws: 如果启用VAD失败，抛出AECAudioStreamError
     */
    public func toggleVoiceActivityDetection(enable: Bool) throws {
        // 获取当前设备ID
        var propertySize = UInt32(MemoryLayout<AudioObjectID>.size)
        var defaultInputDevice: AudioObjectID = 0
        
        var propertyAddress = AudioObjectPropertyAddress(
            mSelector: kAudioHardwarePropertyDefaultInputDevice,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        
        var status = AudioObjectGetPropertyData(
            AudioObjectID(kAudioObjectSystemObject),
            &propertyAddress,
            0,
            nil,
            &propertySize,
            &defaultInputDevice
        )
        
        guard status == kAudioHardwareNoError else {
            logger.error("获取默认输入设备失败")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        self.deviceID = defaultInputDevice
        
        // 设置VAD启用状态
        var vadEnableAddress = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyVoiceActivityDetectionEnable,
            mScope: kAudioDevicePropertyScopeInput,
            mElement: kAudioObjectPropertyElementMain
        )
        
        var shouldEnable: UInt32 = enable ? 1 : 0
        status = AudioObjectSetPropertyData(
            deviceID,
            &vadEnableAddress,
            0,
            nil,
            UInt32(MemoryLayout<UInt32>.size),
            &shouldEnable
        )
        
        guard status == kAudioHardwareNoError else {
            logger.error("设置VAD状态失败")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        isVoiceActivityDetectionEnabled = enable
        
        // 如果启用VAD，注册状态监听器
        if enable {
            var vadStateAddress = AudioObjectPropertyAddress(
                mSelector: kAudioDevicePropertyVoiceActivityDetectionState,
                mScope: kAudioDevicePropertyScopeInput,
                mElement: kAudioObjectPropertyElementMain
            )
            
            status = AudioObjectAddPropertyListener(
                deviceID,
                &vadStateAddress,
                vadStateListenerCallback,
                Unmanaged.passUnretained(self).toOpaque()
            )
            
            guard status == kAudioHardwareNoError else {
                logger.error("添加VAD状态监听器失败")
                throw AECAudioStreamError.osStatusError(status: status)
            }
        } else {
            // 如果禁用VAD，移除状态监听器
            var vadStateAddress = AudioObjectPropertyAddress(
                mSelector: kAudioDevicePropertyVoiceActivityDetectionState,
                mScope: kAudioDevicePropertyScopeInput,
                mElement: kAudioObjectPropertyElementMain
            )
            
            AudioObjectRemovePropertyListener(
                deviceID,
                &vadStateAddress,
                vadStateListenerCallback,
                Unmanaged.passUnretained(self).toOpaque()
            )
        }
    }

    private func startGraph() throws {
        var status = AUGraphInitialize(graph!)
        guard status == noErr else {
            throw AECAudioStreamError.osStatusError(status: status)
        }
        status = AUGraphStart(graph!)
        guard status == noErr else {
            throw AECAudioStreamError.osStatusError(status: status)
        }
    }
    
    private func startAudioUnit() throws {
        guard let audioUnit = audioUnit else {return}
        let status = AudioOutputUnitStart(audioUnit)
        guard AudioOutputUnitStart(audioUnit) == noErr else {
            throw AECAudioStreamError.osStatusError(status: status)
        }
    }
    
    private func createAUGraphForAudioUnit() throws {
        // Create AUGraph
        var status = NewAUGraph(&graph)
        guard status == noErr else {
            logger.error("Error in [NewAUGraph]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        // Create nodes and add to the graph
        var inputcd = AudioComponentDescription()
        inputcd.componentType = kAudioUnitType_Output
        inputcd.componentSubType = kAudioUnitSubType_VoiceProcessingIO
        inputcd.componentManufacturer = kAudioUnitManufacturer_Apple
        
        // Add the input node to the graph
        var remoteIONode: AUNode = 0
        status = AUGraphAddNode(graph!, &inputcd, &remoteIONode)
        guard status == noErr else {
            logger.error("AUGraphAddNode failed")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        // Open the graph
        status = AUGraphOpen(graph!)
        guard status == noErr else {
            logger.error("AUGraphOpen failed")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        // Get a reference to the input node
        status = AUGraphNodeInfo(graph!, remoteIONode, &inputcd, &audioUnit)
        guard status == noErr else {
            logger.error("AUGraphNodeInfo failed")
            throw AECAudioStreamError.osStatusError(status: status)
        }
    }
    
    /// Create a canonical StreamDescription for kAudioUnitSubType_VoiceProcessingIO
    /// - Parameter sampleRate: sample rate
    /// - Returns: canonical AudioStreamBasicDescription
    static func canonicalStreamDescription(sampleRate: Float64) -> AudioStreamBasicDescription {
        var canonicalBasicStreamDescription = AudioStreamBasicDescription()
        canonicalBasicStreamDescription.mSampleRate = sampleRate
        canonicalBasicStreamDescription.mFormatID = kAudioFormatLinearPCM
        canonicalBasicStreamDescription.mFormatFlags = kAudioFormatFlagIsSignedInteger | kAudioFormatFlagIsPacked
        canonicalBasicStreamDescription.mFramesPerPacket = 1
        canonicalBasicStreamDescription.mChannelsPerFrame = 1 //Mono Channel
        canonicalBasicStreamDescription.mBitsPerChannel = 16
        canonicalBasicStreamDescription.mBytesPerPacket = 2
        canonicalBasicStreamDescription.mBytesPerFrame = 2
        return canonicalBasicStreamDescription
    }
    
    
    private func configureAudioUnit() throws {
        guard let audioUnit = audioUnit else {return}
        // Bus 0 provides output to hardware and bus 1 accepts input from hardware. See the Voice-Processing I/O Audio Unit Properties(`kAudioUnitSubType_VoiceProcessingIO`) for the identifiers for this audio unit’s properties.
        let bus_0_output: AudioUnitElement = 0
        let bus_1_input: AudioUnitElement = 1
        
        var enableInput: UInt32 = 1
        var status = AudioUnitSetProperty(audioUnit, kAudioOutputUnitProperty_EnableIO, kAudioUnitScope_Input, bus_1_input, &enableInput, UInt32(MemoryLayout.size(ofValue: enableInput)))
        guard status == noErr else {
            AudioComponentInstanceDispose(audioUnit)
            logger.error("Error in [AudioUnitSetProperty|kAudioUnitScope_Input]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        var enableOutput: UInt32 = enableRendererCallback ? 1 : 0
        status = AudioUnitSetProperty(audioUnit, kAudioOutputUnitProperty_EnableIO, kAudioUnitScope_Output, bus_0_output, &enableOutput, UInt32(MemoryLayout.size(ofValue: enableOutput)))
        guard status == noErr else {
            AudioComponentInstanceDispose(audioUnit)
            logger.error("Error in [AudioUnitSetProperty|kAudioUnitScope_Output]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        status = AudioUnitSetProperty(audioUnit, kAudioUnitProperty_StreamFormat, kAudioUnitScope_Output, bus_1_input, &self.streamBasicDescription, UInt32(MemoryLayout<AudioStreamBasicDescription>.size))
        guard status == noErr else {
            AudioComponentInstanceDispose(audioUnit)
            logger.error("Error in [AudioUnitSetProperty|kAudioUnitProperty_StreamFormat|kAudioUnitScope_Output]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        
        status = AudioUnitSetProperty(audioUnit, kAudioUnitProperty_StreamFormat, kAudioUnitScope_Input, bus_0_output, &self.streamBasicDescription, UInt32(MemoryLayout<AudioStreamBasicDescription>.size))
        guard status == noErr else {
            AudioComponentInstanceDispose(audioUnit)
            logger.error("Error in [AudioUnitSetProperty|kAudioUnitProperty_StreamFormat|kAudioUnitScope_Input]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        // Set the input callback for the audio unit
        var inputCallbackStruct = AURenderCallbackStruct()
        inputCallbackStruct.inputProc = kInputCallback
        inputCallbackStruct.inputProcRefCon = Unmanaged.passUnretained(self).toOpaque()
        status = AudioUnitSetProperty(audioUnit, kAudioOutputUnitProperty_SetInputCallback, kAudioUnitScope_Input, bus_1_input, &inputCallbackStruct, UInt32(MemoryLayout.size(ofValue: inputCallbackStruct)))
        guard status == noErr else {
            logger.error("Error in [AudioUnitSetProperty|kAudioOutputUnitProperty_SetInputCallback|kAudioUnitScope_Input]")
            throw AECAudioStreamError.osStatusError(status: status)
        }
        
        if enableRendererCallback {
            // Set the input callback for the audio unit
            var outputCallbackStruct = AURenderCallbackStruct()
            outputCallbackStruct.inputProc = kRenderCallback
            outputCallbackStruct.inputProcRefCon = Unmanaged.passUnretained(self).toOpaque()
            status = AudioUnitSetProperty(audioUnit, kAudioUnitProperty_SetRenderCallback, kAudioUnitScope_Output, bus_0_output, &outputCallbackStruct, UInt32(MemoryLayout.size(ofValue: outputCallbackStruct)))
            guard status == noErr else {
                logger.error("Error in [AudioUnitSetProperty|kAudioOutputUnitProperty_SetInputCallback|kAudioUnitScope_Output]")
                throw AECAudioStreamError.osStatusError(status: status)
            }
        }
    }
}

// 添加VAD状态监听回调函数
private func vadStateListenerCallback(
    inObjectID: AudioObjectID,
    inNumberAddresses: UInt32,
    inAddresses: UnsafePointer<AudioObjectPropertyAddress>,
    inClientData: UnsafeMutableRawPointer?) -> OSStatus {
        
        let audioStream = Unmanaged<AECAudioStream>.fromOpaque(inClientData!).takeUnretainedValue()
        
        var vadStateAddress = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyVoiceActivityDetectionState,
            mScope: kAudioDevicePropertyScopeInput,
            mElement: kAudioObjectPropertyElementMain
        )
        
        var voiceDetected: UInt32 = 0
        var propertySize = UInt32(MemoryLayout<UInt32>.size)
        let status = AudioObjectGetPropertyData(
            inObjectID,
            &vadStateAddress,
            0,
            nil,
            &propertySize,
            &voiceDetected
        )
        
        if status == kAudioHardwareNoError {
            let isVoiceActive = voiceDetected == 1
            audioStream.updateVoiceDetectionState(isVoiceActive)
        }
        
        return status
}


private func kInputCallback(inRefCon:UnsafeMutableRawPointer,
                            ioActionFlags:UnsafeMutablePointer<AudioUnitRenderActionFlags>,
                            inTimeStamp:UnsafePointer<AudioTimeStamp>,
                            inBusNumber:UInt32,
                            inNumberFrames:UInt32,
                            ioData:UnsafeMutablePointer<AudioBufferList>?) -> OSStatus {
    
    let audioMgr = unsafeBitCast(inRefCon, to: AECAudioStream.self)
    
    guard let audioUnit = audioMgr.audioUnit else {
        return kAudio_ParamError
    }
    
    let audioBuffer = AudioBuffer(mNumberChannels: 1, mDataByteSize: 0, mData: nil)
    
    var bufferList = AudioBufferList(mNumberBuffers: 1, mBuffers: audioBuffer)
    
    let status = AudioUnitRender(audioUnit, ioActionFlags, inTimeStamp, 1, inNumberFrames, &bufferList)
    
    guard status == noErr else { return status }
    
    if let buffer = AVAudioPCMBuffer(pcmFormat: audioMgr.streamFormat, bufferListNoCopy: &bufferList), let captureAudioFrameHandler = audioMgr.capturedFrameHandler {
        captureAudioFrameHandler(buffer)
    }
    return kAudio_ParamError
}

private func kRenderCallback(inRefCon:UnsafeMutableRawPointer,
                             ioActionFlags:UnsafeMutablePointer<AudioUnitRenderActionFlags>,
                             inTimeStamp:UnsafePointer<AudioTimeStamp>,
                             inBusNumber:UInt32,
                             inNumberFrames:UInt32,
                             ioData:UnsafeMutablePointer<AudioBufferList>?) -> OSStatus {
    
    let audioMgr = unsafeBitCast(inRefCon, to: AECAudioStream.self)
    
    guard let outSample = ioData?.pointee.mBuffers.mData?.assumingMemoryBound(to: Int16.self) else {
        return kAudio_ParamError
    }
    let bufferLength = ioData!.pointee.mBuffers.mDataByteSize / UInt32(MemoryLayout<Int16>.stride)
    // Zero out buffers
    memset(outSample, 0, Int(bufferLength))
    
    if let rendererClosure = audioMgr.rendererClosure {
        rendererClosure(ioData!, inNumberFrames)
    } else {
        // Renderer callback enabled but not renderrerClosure is assigned.
        return kAudioUnitErr_InvalidParameter
    }
    
    return noErr
}

private var sharedInstance: AECAudioStream? = nil
private var audioDataQueue: AudioDataQueue? = nil

// 将AVAudioPCMBuffer转换为Data
func pcmBufferToData(_ buffer: AVAudioPCMBuffer) -> Data? {
    let audioBuffer = buffer.audioBufferList.pointee.mBuffers
    
    if let mData = audioBuffer.mData {
        let length = Int(audioBuffer.mDataByteSize)
        return Data(bytes: mData, count: length)
    }
    
    return nil
}

@_cdecl("startRecord")
public func startAudioRecord() {
    if (sharedInstance == nil){
        sharedInstance = AECAudioStream(sampleRate: 16000)
        sharedInstance?.voiceActivityHandler = { isVoiceDetected in
            if isVoiceDetected {
                print("检测到语音活动")
            } else {
                print("未检测到语音活动")
            }
        }
    }
    
    if (audioDataQueue == nil) {
        audioDataQueue = AudioDataQueue(capacity: 1024)
    }
    
    guard let instance = sharedInstance else { return }
    
    // 创建文件路径
    //    let documentsDirectory = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask)[0]
    //    let fileName = "audio_recording_\(Date().timeIntervalSince1970).pcm"
    //    let fileURL = documentsDirectory.appendingPathComponent(fileName)
    
    // 创建文件句柄
    //    FileManager.default.createFile(atPath: fileURL.path, contents: nil)
    //    let fileHandle = try? FileHandle(forWritingTo: fileURL)
    
    //    print("录音将保存到: \(fileURL.path)")
    do {
        try instance.toggleVoiceActivityDetection(enable: true)
    } catch {

        print("启动VAD失败: \(error)")
    }
    
    Task {
        for try await pcmBuffer in instance.startAudioStream(enableAEC: true) {
            if let data = pcmBufferToData(pcmBuffer) {
                let isVoiceActive = instance.isVoiceDetected
                _ = audioDataQueue?.push(data: data, isVoiceActive: isVoiceActive)
            }
        }
        
        // 关闭文件
        //        try? fileHandle?.close()
    }
}

@_cdecl("stopRecord")
public func stopAudioRecord() {
    if (sharedInstance == nil) {
        return
    }
    do {
        try sharedInstance?.stopAudioUnit()
    } catch {
        print("停止音频单元失败: \(error)")
    }
    
}

@_cdecl("getAudioData")
public func getAudioData(_ sizePtr: UnsafeMutablePointer<Int>, _ isVoiceActivePtr: UnsafeMutablePointer<Bool>) -> UnsafeMutablePointer<UInt8>? {
    guard let packet = audioDataQueue?.pop() else {
        sizePtr.pointee = 0
        isVoiceActivePtr.pointee = false
        return nil
    }
    
    let length = packet.audioData.count
    sizePtr.pointee = length
    isVoiceActivePtr.pointee = packet.isVoiceActive
    
    let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: length)
    packet.audioData.copyBytes(to: buffer, count: length)
    
    return buffer
}


// 添加一个函数用于释放内存
@_cdecl("freeAudioData")
public func freeAudioData(_ buffer: UnsafeMutablePointer<UInt8>?) {
    buffer?.deallocate()
}
