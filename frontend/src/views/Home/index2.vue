<script setup lang="ts">
import router from "@/router.ts";
import {
    DownloadOutlined, FileMarkdownOutlined, SettingOutlined,
    AudioOutlined, DeleteOutlined, FileTextOutlined,
    ArrowRightOutlined, ContainerOutlined, UploadOutlined
} from "@ant-design/icons-vue";
import { test_server } from "@/config/client_config.ts";
import axios from "axios";
import { nextTick, onMounted, onUnmounted, reactive, ref, createVNode, computed, watch } from "vue";

import { useSessionStore, downloadSessionData } from "@/stores/session";
import type { SessionSummary, SessionNode } from '@/stores/session'; // 导入类型
import { useSettingsStore } from "@/stores/config.ts";
const sessionStore = useSessionStore()
const settingsStore = useSettingsStore();
// https://github.surmon.me/videojs-player video.js debug page;
// const base_url = 'http://192.168.110.102:8000'


const host = import.meta.env.PROD ? window.location.host : test_server
// const pathname = window.location.pathname
let ws_prefix = 'ws'
if (host.startsWith('127.0.0.1') || host.startsWith('localhost')) {
    ws_prefix = 'ws'
} else {
    ws_prefix = 'wss'
}
const ws_url = `${ws_prefix}://` + host + `/ws?`
console.warn('ws_url: ', ws_url)

const sock = ref(null)
const startWebSock = async (lang_str: string) => {
    console.warn('start websocket ...')
    // 确保在创建 WebSocket 连接之前关闭已有连接
    // @ts-ignore
    if (sock.value && sock.value.readyState !== WebSocket.CLOSED) {
        // @ts-ignore
        sock.value.close();
    }

    // const socket_url = `${ws_url}${lang_str}${'&vad=' + vadValueRef.value}`
    const socket_url = `${ws_url}${lang_str}`
    // @ts-ignore
    sock.value = new WebSocket(socket_url)
    // @ts-ignore
    sock.value.binaryType = "arraybuffer";
    console.warn('created web socket ...')
    // @ts-ignore
    sock.value.addEventListener('open', () => {
        console.log('WebSocket 连接成功');
        startAudioCapture(); // WebSocket 连接成功后开始音频捕获
        isRecording.value = true; // 连接成功时自动开始录音
    });
    // @ts-ignore
    sock.value.addEventListener('close', () => {
        console.log('WebSocket 连接已关闭');
    });
    // @ts-ignore
    sock.value.onclose = (event: any) => {
        console.log('code:', event.code, 'reason:', event.reason, 'wasClean:', event.wasClean)
        // https://www.cnblogs.com/gxp69/p/11736749.html
        console.log('WebSocket 连接已关闭:', event);
    };
    // @ts-ignore
    sock.value.addEventListener('error', (error) => {
        console.error('WebSocket 连接错误:', error);
    });
    // @ts-ignore
    sock.value.addEventListener('message', (event) => {
        try { // 添加 try-catch 保证 JSON 解析失败不中断程序
            const data = JSON.parse(event.data)
            console.log('WebSocket 收到消息:', data);
            if (data && data['result']) {
                updateViewData(data['result'])
            }
        } catch (e) {
            console.error("解析 WebSocket 消息失败:", e, "原始数据:", event.data);
        }
    });
}

const stopWebSock = async () => {
    if (sock.value) {
        console.log("主动关闭 WebSocket 连接");
        // @ts-ignore
        sock.value.close(1000, "User closed connection"); // 使用标准关闭代码
        sock.value = null;
    }
}

const audioStreamRef = ref<MediaStream | null>(null);
const recorderRef = ref(null);
const audioContextRef = ref<AudioContext | null>(null);
const sourceNodeRef = ref(null)
const processorNodeRef = ref(null)
const isRecording = ref<boolean>(false);

// 启动音频捕获
const startAudioCapture = async () => {
    try {
        // 检查 AudioContext 是否支持
        // @ts-ignore
        if (!window.AudioContext && !window.webkitAudioContext) {
            alert("浏览器不支持 Web Audio API");
            throw new Error("浏览器不支持 Web Audio API");
        }

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                // @ts-ignore
                sampleRate: 16000,
                channelCount: 1,
                // echoCancellation: true,
                // noiseSuppression: true,
                // autoGainControl: true,
            },
        });
        audioStreamRef.value = stream;

        // 创建 AudioContext，指定采样率为 16kHz
        const audioContext = new AudioContext({ sampleRate: 16000 });
        audioContextRef.value = audioContext;

        // 创建媒体流源节点
        const source = audioContext.createMediaStreamSource(stream);
        // @ts-ignore
        sourceNodeRef.value = source;

        // 创建脚本处理器节点
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        // @ts-ignore
        processorNodeRef.value = processor;

        // 连接节点
        source.connect(processor);
        processor.connect(audioContext.destination);

        // 设置音频处理回调
        processor.onaudioprocess = (e: AudioProcessingEvent) => {
            // @ts-ignore
            if (!isRecording.value || !sock.value || sock.value.readyState !== WebSocket.OPEN) return;

            const input = e.inputBuffer.getChannelData(0);
            const buffer = new Int16Array(input.length);

            for (let i = 0; i < input.length; i++) {
                buffer[i] = Math.max(-1, Math.min(1, input[i])) * 0x7FFF;
            }

            sendAudioChunk(buffer);
        };

        isRecording.value = true;
        console.log('音频捕获已启动');

    } catch (err) {
        console.error('音频捕获失败:', err);
    }
}

const sendAudioChunk = (audioBuffer: any) => {
    // @ts-ignore
    if (sock.value && sock.value.readyState === WebSocket.OPEN) {
        // @ts-ignore
        sock.value.send(audioBuffer);
        // console.log('WebSocket send audio chunk success'); // 减少日志量
    } else {
        console.error('WebSocket 未连接或未打开，无法发送音频');
        // 考虑停止录音
        // handleRecordingSwitch(false);
    }
};


// 请求录音权限并开始录音
const requirePermissionAction = async () => {
    console.log('requirePermissionAction');
    try {
        // 确保 WebSocket 连接已建立
        // @ts-ignore
        if (!sock.value || sock.value.readyState !== WebSocket.OPEN) {
            console.log('current lang_str : ', transLanguageValue.value)
            const lang_str = transLanguageValue.value

            resetViewData();
            await startWebSock(lang_str);
        } else {
            // 如果 WebSocket 已经连接，可能只需要重新开始音频捕获（如果之前停止了）
            if (!audioStreamRef.value) {
                await startAudioCapture();
            }
        }
    } catch (e: any) {
        isRecording.value = false; // 确保出错时关闭开关
        console.log('Error accessing microphone: ', e);
    }
};


// 格式化时间戳函数
const formatTimestamp = (ms: number): string => {
    const date = new Date(ms);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // 月份从 0 开始，需要 +1
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return `${year}-${month}-${day}-${hours}:${minutes}:${seconds}`;
}

onMounted(() => {
    console.log('[translator]: mounted')
    fontSizeRef.value = settingsStore.$state.fs
    maxWidthRef.value = settingsStore.$state.width_max
    vadValueRef.value = settingsStore.$state.vad

    if (sessionStore.isSessionActive) {
        console.warn("检测到上次会话未正常结束，重置状态。");
        sessionStore.$reset(); // 或者手动重置相关状态
        // isRecording.value = false; // 确保 UI 同步
    }
})

onUnmounted(() => {
    console.log('[HomePage]: unmounted')
    if (sock.value) {
        // @ts-ignore
        sock.value.close();
    }
    if (recorderRef.value) {
        stopRecording();
        sessionStore.endSession(); // 结束当前会话
    }
})

// 停止录音
const stopRecording = () => {
    isRecording.value = false;

    stopWebSock();
    console.log('音频捕获已停止');

    if (processorNodeRef.value) {
        // @ts-ignore
        processorNodeRef.value.disconnect();
        processorNodeRef.value = null;
    }

    if (sourceNodeRef.value) {
        // @ts-ignore
        sourceNodeRef.value.disconnect();
        sourceNodeRef.value = null;
    }

    if (audioStreamRef.value) {
        audioStreamRef.value.getTracks().forEach(track => track.stop());
        audioStreamRef.value = null;
    }

    if (audioContextRef.value) {
        // @ts-ignore
        audioContextRef.value.close();
        audioContextRef.value = null;
    }

    // current_node_text.value = "";
    // current_node_trans_text.value = "";
    // current_node_seg_id.value = "";

    // 添加当前节点到会话记录；
    const finalNode: SessionNode = {
        id: current_node_seg_id.value || crypto.randomUUID(), // 使用后端 ID 或生成一个
        text: current_node_text.value,
        translatedText: current_node_trans_text.value,
        timestamp: Date.now(),
    };
    sessionStore.addNode(finalNode);

    console.log('录音已停止');
};


const handleLanguageChange = async (value: string) => {
    console.log(`selected ${value}`);
    isRecording.value = false;
    await stopRecording();
    sessionStore.endSession();

    console.log('new lang_str: ', value)
    console.log('trans_lang : ', transLanguageValue.value)
    // requirePermissionAction();
};


const handleRecordingSwitch = (checked: boolean) => {
    isRecording.value = checked;
    if (checked) {
        isRecording.value = true; // 更新UI状态
        requirePermissionAction();
        sessionStore.startSession(); // 开始新的会话
    } else {
        isRecording.value = false; // 更新UI状态
        stopRecording();
        sessionStore.endSession();
    }
};


const transLanguageValue = ref("from=en&to=zh");
const options = [
    { value: "from=en&to=zh", label: "English -> Chinese" },
    { value: "from=zh&to=en", label: "Chinese -> English" },
];

// @ts-ignore
const completedNodesForDisplay: any = reactive([])

const current_node_text = ref("");
const current_node_trans_text = ref("");
const current_node_seg_id = ref("");

const updateViewData = (data: any) => {
    console.log('updateViewData: ', data)
    if (data) {
        const { context, from, to, seg_id, partial, tranContent } = data;

        if (partial == true) {
            current_node_text.value = context;
            current_node_trans_text.value = tranContent;
            current_node_seg_id.value = seg_id;

            return;
        } else {
            // partial == false，表示一句话结束
            const finalNode: SessionNode = {
                id: seg_id || crypto.randomUUID(), // 使用后端 ID 或生成一个
                text: context,
                translatedText: tranContent,
                timestamp: Date.now(),
            };

            sessionStore.addNode(finalNode);

            if (completedNodesForDisplay.length > 100) {
                // 控制显示列表长度，避免 DOM 过多
                completedNodesForDisplay.splice(0, 40);
            }
            completedNodesForDisplay.push(finalNode);
            current_node_text.value = "";
            current_node_trans_text.value = "";
            current_node_seg_id.value = "";
        }
    }

    scrollToBottom();
}

const resetViewData = () => {
    completedNodesForDisplay.splice(0, completedNodesForDisplay.length); // 清空显示列表
    current_node_text.value = "";
    current_node_trans_text.value = "";
    current_node_seg_id.value = "";
}

const downloadText2 = async (sid: string, nodes: SessionNode[]) => {
    // @ts-ignore
    // 将数组中的每个字符串元素用换行符连接起来
    // const textContent = all_nodes.join('\n');
    const textContent = nodes.map((node: any) => {
        return `[src]: ${node.text}\n${"-".repeat(80)}\n[dst]: ${node.translatedText}\n\n`
    }).join('\n');
    // 创建 Blob 时指定 MIME 类型为 text/plain
    const blob = new Blob([textContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    // 修改下载文件名为 .txt
    a.download = `${sid}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}


const downloadText = (sid: number, nodes: SessionNode[]) => { // Removed async as it's not needed here
    try {
        if (!nodes || nodes.length === 0) {
            console.warn("No nodes provided for download.");
            alert("No content available to download for this session.");
            return;
        }

        const textContent = nodes.map((node: SessionNode) => { // Use correct type SessionNode
            // Safely access properties, provide fallback for undefined translatedText
            const srcText = node.text || '(No original text)';
            const dstText = node.translatedText || '(No translation)';
            return `[src]: ${srcText}\n${"-".repeat(80)}\n[dst]: ${dstText}\n\n`;
        }).join(''); // Join without extra newline, as \n\n is already added

        if (!textContent.trim()) {
            console.warn("Generated text content is empty.");
            alert("Generated content is empty, cannot download.");
            return;
        }

        // Create Blob with UTF-8 charset
        const blob = new Blob([textContent], { type: "text/plain;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");

        a.href = url;
        a.download = `${formatTimestamp(sid)}.txt`; // Ensure filename is set
        a.style.display = 'none'; // Hide the element

        document.body.appendChild(a);
        console.log(`Attempting to click download link for ${sid}.txt`);
        a.click(); // Trigger the download

        // Delay cleanup to ensure download initiation
        setTimeout(() => {
            try {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                console.log(`Cleaned up resources for ${sid}.txt`);
            } catch (cleanupError) {
                console.error("Error during download cleanup:", cleanupError);
            }
        }, 100); // Delay cleanup by 100ms

    } catch (error) {
        console.error("Error creating download file:", error);
        alert("An error occurred while preparing the download.");
    }
}


const placeholder_zh = "体验前请检查麦克风是否可用，指定音频语言、译文语言，点击开关按钮开始录音，即可实时获取识别及翻译的文字。"
const placeholder_en = "Please check if the microphone is available before the experience, specify the audio language and translation language, click the switch button to start recording, and you can get the recognized and translated text in real time."


const transListRef = ref(null);
// 自动滚动到底部的函数
const scrollToBottom = () => {
    nextTick(() => {
        if (transListRef.value) {
            // @ts-ignore
            transListRef.value.scrollTop = transListRef.value.scrollHeight + 144;
        }
    });
};

watch(() => [...completedNodesForDisplay], () => {
    scrollToBottom();
}, { deep: true });

watch(() => current_node_trans_text.value, () => {
    scrollToBottom();
}), { deep: true };

// config
const configVisible = ref(false);
const showConfig = () => {
    configVisible.value = true;
}
const hideConfig = () => {
    configVisible.value = false;
    if (vadValueRef.value != settingsStore.$state.vad) {
        settingsStore.$state.vad = vadValueRef.value

        if (recorderRef.value) {
            stopRecording();
            sessionStore.endSession();
        }
    }
}

const vadValueRef = ref(0.3);
const maxWidthRef = ref(false);
const fontSizeRef = ref('trans-font-size-18')
const showRealTimeBufferRef = ref(true)
const showSourceLanguageOnlyRef = ref(false);

const onFontSizeChange = (e: any) => {
    console.log('onFontSizeChange', e.target.value)
    fontSizeRef.value = e.target.value
    settingsStore.$state.fs = e.target.value
}

const sessionsModalVisible = ref(false);


// Modal 中下载按钮的处理函数
const handleDownloadSession = (summary: SessionSummary) => {
    console.log(`请求下载会话: ${summary.startTime}`);
    const nodes = sessionStore.loadSessionContent(summary.startTime);
    if (nodes) {
        // 弹出格式选择或直接下载 JSON
        // const format = prompt("选择下载格式: 'json' 或 'txt'", "json");
        // if (format === 'json' || format === 'txt') {
        //     downloadSessionData(summary.startTime, nodes, format);
        // }
        // downloadSessionData(summary.startTime, nodes, 'json'); // 默认下载 JSON
        downloadText(summary.startTime, nodes);

    } else {
        alert(`无法加载会话 ${summary.startTime} 的内容进行下载。`);
    }
}

// Modal 中删除按钮的处理函数
const handleDeleteSession = (summary: SessionSummary) => {
    if (confirm(`确定要删除开始于 ${new Date(summary.startTime).toLocaleString()} 的会话吗？\n标题: ${summary.title}`)) {
        sessionStore.deleteSession(summary.startTime);
        console.log(`已删除会话: ${summary.startTime}`);
    }
}

// 计算属性，用于模板中方便访问排序后的摘要
const sortedSummaries = computed(() => sessionStore.sortedSessionSummaries);


</script>

<template>
    <div class="view-wrapper">
        <div :class="['content-wrapper', maxWidthRef ? 'wrapper-width-auto': 'wrapper-width-fixed']">
            <div style="margin-top: 0; padding: 0px">
                <a-card :bordered="false" style="width: 100%;min-width: 100%;">
                    <div v-show="!(completedNodesForDisplay.length || current_node_text)" class="chat-box-placeholder">
                        {{
                        placeholder_en }}</div>
                    <div v-show="(completedNodesForDisplay.length || current_node_text)" class="trans-list"
                        ref="transListRef">
                        <div v-for="node in completedNodesForDisplay" :key="node.id" :class="['node']"
                            :data-seg-id="node.id">
                            <div
                                :class="[showSourceLanguageOnlyRef ? 'trans-dst-lang' : 'trans-src-lang', fontSizeRef]">
                                {{ node.text }}</div>
                            <div v-show="!showSourceLanguageOnlyRef" :class="['trans-dst-lang', fontSizeRef]">{{
                                node.translatedText }}</div>
                        </div>

                        <div v-show="showRealTimeBufferRef" class="node current_node"
                            :key="current_node_seg_id">
                            <div
                                :class="[showSourceLanguageOnlyRef ? 'trans-dst-lang' : 'trans-src-lang', fontSizeRef]">
                                {{ current_node_text }}</div>
                            <div v-show="!showSourceLanguageOnlyRef" :class="['trans-dst-lang', fontSizeRef]">{{
                                current_node_trans_text }}</div>
                        </div>


                    </div>
                    <template #actions>
                        <div class="actions-box">
                            <div class="left-actions">
                                <a-popover v-model:open="configVisible" placement="topLeft" trigger="click">
                                    <template #content>
                                        <div class="config-content">
                                            <div v-if="false" class="config-block">
                                                <h4 style="font-weight: 500;">Speaking Speed:</h4>
                                                <a-radio-group v-model:value="vadValueRef">
                                                    <a-radio :value="0.1">fastest</a-radio>
                                                    <a-radio :value="0.3">fast</a-radio>
                                                    <a-radio :value="0.5">normal</a-radio>
                                                    <a-radio :value="0.75">slow</a-radio>
                                                    <a-radio :value="1">slowest</a-radio>
                                                </a-radio-group>
                                            </div>
                                            <div v-if="false" class="config-block">
                                                <h4 style="font-weight: 500;">Page Max Width:</h4>
                                                <a-switch v-model:checked="maxWidthRef" />
                                            </div>
                                            <div class="config-block">
                                                <h4 style="font-weight: 500;">Show Realtime Buffer:</h4>
                                                <a-switch v-model:checked="showRealTimeBufferRef" />
                                            </div>
                                            <div class="config-block">
                                                <h4 style="font-weight: 500;">Show Source Language Only:</h4>
                                                <a-switch v-model:checked="showSourceLanguageOnlyRef" />
                                            </div>
                                            <div class="config-block">
                                                <h4 style="font-weight: 500;">Text Font Size:</h4>
                                                <a-radio-group v-model:value="fontSizeRef" @change="onFontSizeChange">
                                                    <a-radio :value="'trans-font-size-16'">Small</a-radio>
                                                    <a-radio :value="'trans-font-size-18'">Default</a-radio>
                                                    <a-radio :value="'trans-font-size-20'">Normal</a-radio>
                                                    <a-radio :value="'trans-font-size-24'">Medium</a-radio>
                                                    <a-radio :value="'trans-font-size-32'">Large</a-radio>
                                                </a-radio-group>
                                            </div>
                                        </div>
                                        <div style="display: flex; justify-content: end;">
                                            <a-button type="primary" @click="hideConfig">Done</a-button>
                                        </div>
                                    </template>
                                    <a-button type="dashed" shape="circle" size="middle" @click="showConfig">
                                        <template #icon>
                                            <SettingOutlined />
                                        </template>
                                    </a-button>
                                </a-popover>

                                <a-select v-model:value="transLanguageValue" style="width: 240px;"
                                    placeholder="Select Language" :options="options"
                                    @change="handleLanguageChange"></a-select>
                                <a-button type="dashed" shape="circle" size="middle"
                                    @click="sessionsModalVisible = true">
                                    <template #icon>
                                        <FileTextOutlined />
                                    </template>
                                </a-button>
                                <a-modal v-model:open="sessionsModalVisible" width="85vh" title="Session History"
                                    centered :closable="true" ok-text="OK" @ok="sessionsModalVisible = false"
                                    :footer="null">
                                    <div class="sessions">
                                        <div v-if="sortedSummaries.length > 0">
                                            <div v-for="summary in sortedSummaries" :key="summary.startTime"
                                                class="session-node">
                                                <div class="content">
                                                    <!-- <div class="content-title">{{ summary.title }}</div> -->
                                                    <div class="content-text">
                                                        Start at: {{ new Date(summary.startTime).toLocaleString() }} ({{
                                                        summary.nodeCount }} items)
                                                    </div>
                                                    <div class="content-outline">
                                                        <div v-if="summary.outline.length > 0">
                                                            <div class="outline-line"
                                                                v-for="(line, index) in summary.outline" :key="index">{{
                                                                line
                                                                }}</div>
                                                        </div>
                                                        <i v-else>(No outline available)</i>
                                                    </div>
                                                </div>
                                                <div class="session-action">
                                                    <!-- <a-popconfirm title="Are you sure you want to delete this session?"
                                                    ok-text="Yes" cancel-text="No"
                                                    @confirm="handleDeleteSession(summary)">
                                                    <a-button type="danger" shape="circle" size="middle"
                                                        style="margin-left: 8px;">
                                                        <template #icon>
                                                            <DeleteOutlined />
                                                        </template>
                                                    </a-button>
                                                </a-popconfirm> -->
                                                    <a-button danger type="dashed" shape="circle" size="middle"
                                                        @click="handleDeleteSession(summary)" style="margin-left: 8px;">
                                                        <template #icon>
                                                            <DeleteOutlined />
                                                        </template>
                                                    </a-button>
                                                    <a-button type="dashed" shape="circle" size="middle"
                                                        @click="handleDownloadSession(summary)">
                                                        <template #icon>
                                                            <DownloadOutlined />
                                                        </template>
                                                    </a-button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </a-modal>
                                <!-- <a-popconfirm title="download session text content?" @confirm="downloadClick"
                                    ok-text="Yes" cancel-text="No">
                                    <template #icon>
                                        <FileMarkdownOutlined style="color: red" />
                                    </template>
                                    <a-button type="dashed" shape="circle" size="middle">
                                        <template #icon>
                                            <DownloadOutlined />
                                        </template>
                                    </a-button>
                                </a-popconfirm> -->
                            </div>

                            <a-switch key="switcher" size="large" type="danger" checked-children="ON"
                                un-checked-children="OFF" v-model:checked="isRecording" @change="handleRecordingSwitch">
                            </a-switch>
                            <!-- <div class="right-actions">
                                <a-button type="dashed" shape="circle" size="middle" @click="downloadClick">
                                    <template #icon>
                                        <DownloadOutlined />
                                    </template>
                                </a-button>
                                <a-switch key="switcher" size="large" type="danger" checked-children="ON"
                                    un-checked-children="OFF" v-model:checked="isRecording"
                                    @change="handleRecordingSwitch">
                                </a-switch>
                            </div> -->

                        </div>
                    </template>
                </a-card>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.config-content {
    width: 320px;
    margin:12px;

    .config-block {
        margin: 12px;
        padding-bottom: 12px;
    }
}

.sessions {
    width: 100%;
    height: 100%;
    min-height: 50vh;
    max-height: 85vh;
    overflow-y: scroll;
    margin-top:24px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;

    .session-node {
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        margin-bottom: 12px;
        background-color: rgba(240, 241, 247, 1);
        border-radius: 4px;

        .content {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: self-start;

            .content-title {
                font-size: 18px;
                font-weight: bold;
                color: #2e2f33;
            }

            .content-text {
                font-size: 18px;
                font-weight: 500;
                color: #2e2f33;
            }
            .content-outline {
                width: 100%;

                .outline-line {
                    font-size: 16px;
                    font-weight: 500;
                    color: #909299;
                    margin: 8px 0 4px 0;
                }
            }
        }

        .session-action {
            width: 96px;
            display: flex;
            justify-content: space-around;
            align-items: center;

            .ant-btn-primary {
                background-color: #1890ff !important;
                border-color: #1890ff !important;
            }
        }
    }
}

.view-wrapper {
    width: 100%;
    height: 100%;
    background-color: #fff;

    .wrapper-width-fixed {
        width: 100%;
    }

    .wrapper-width-auto {
        width: 100vw;
    }

    .content-wrapper {
        text-align: left;
        max-width: 100vw;
        min-width: 320px;
        margin-bottom: 0;
        height: 100%;
        min-height: auto;
        background-color: rgba(232, 232, 248, 0.8) !important;

        .chat-box {
            width: 100%;
            height: calc(100vh - 112px);

            // border: solid 1px lightgray;
            border-radius: 4px;
            padding: 12px;
            color: #2e2f33;
            font-size: 18px;
        }
        .chat-box-placeholder {
            width: 100%;
            height: calc(100vh - 112px);
            border-radius: 4px;
            padding: 12px;
            font-size: 18px;
            color: #a4a6ac;
        }

        .actions-box {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 0 36px;
            height: 48px;

            .left-actions {
                display: flex;
                align-items: center;
                justify-content: space-between;
                // width: 288px;
                width: 332px;
            }

            .right-actions {
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 108px;
            }
        }

        .trans-list {
            overflow-y: auto;
            width: 100%;
            height: calc(100vh - 112px);

            scrollbar-width: none;
            -ms-overflow-style: none;
            &::-webkit-scrollbar {
                display: none;
            }

            .node {
                margin-bottom: 36px;
                width: 100% !important;
                transition: all 0.3s ease;

                .trans-time {
                    font-size: 14px;
                    color: #c4c6cc;
                }

                .trans-font-size-16 {
                    font-size: 16px;
                }
                .trans-font-size-18 {
                    font-size: 18px;
                }

                .trans-font-size-20 {
                    font-size: 20px;
                }

                .trans-font-size-32 {
                    font-size: 32px;
                }

                .trans-font-size-24 {
                    font-size: 24px;
                }


                .trans-src-lang {
                    // font-size: 18px;
                    color: #909299;
                    font-weight: 500;
                }

                .trans-dst-lang {
                    // font-size: 18px;
                    color: #2e2f33;
                    font-weight: 600;
                }
            }

            .current_node {
                background-color: rgba(240, 241, 247, 1);
                padding: 8px 4px;
                min-height: 68px;
            }

        }
    }
}

// 动画关键帧定义 - 添加这部分
@keyframes highlight {
    0% {
        background-color: transparent;
    }

    50% {
        background-color: rgba(255, 241, 206, 0.5);
    }

    100% {
        background-color: transparent;
    }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
