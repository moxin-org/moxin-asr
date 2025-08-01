<script setup lang="ts">

import router from "@/router.ts";
import { useSettingsStore } from "@/stores/config.ts";
import { onMounted, onUnmounted, ref, reactive } from "vue";
import { SettingTwoTone } from "@ant-design/icons-vue";
import DynamicBall from "@/views/Home/Components/DynamicBall.vue";
import ChatText from "@/views/Home/Components/ChatText.vue";
import axios from "axios";
import { test_server } from "@/config/client_config.ts";

const base_url = axios.defaults.baseURL

const settingsStore = useSettingsStore()

import mic_on from "@/assets/microphone.png"
import mic_off from "@/assets/microphone_off.png"
import text_on from "@/assets/text.png"
import text_off from "@/assets/text_off.png"
import close from "@/assets/close.png"
import download from "@/assets/download.png"

const host = import.meta.env.PROD ? window.location.host : test_server

let ws_prefix = 'ws'
if (host.startsWith('127.0.0.1') || host.startsWith('localhost')) {
    ws_prefix = 'ws'
} else {
    ws_prefix = 'wss'
}
const ws_url = `${ws_prefix}://` + host + `/api/v1/ws`
console.warn('ws_url: ', ws_url)

const sock = ref(null)
const startWebSock = async () => {
    console.warn('start websocket ...')
    // 确保在创建 WebSocket 连接之前关闭已有连接
    // @ts-ignore
    if (sock.value && sock.value.readyState !== WebSocket.CLOSED) {
        // @ts-ignore
        sock.value.close();
    }

    // const socket_url = `${ws_url}${lang_str}${'&vad=' + vadValueRef.value}`
    const socket_url = `${ws_url}`
    // @ts-ignore
    sock.value = new WebSocket(socket_url)
    // @ts-ignore
    sock.value.binaryType = "arraybuffer";
    console.warn('created web socket ...')
    // @ts-ignore
    sock.value.addEventListener('open', () => {
        console.log('WebSocket 连接成功');
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
            if (data) {
                updateViewData(data)
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

// @ts-ignore
const currentSession: any = reactive([]);

const updateViewData = (data: any) => {
    // console.log('updateViewData: ', data)
    /*
    data = {
        "message_type": "question",
        "session_id": "ae758c85-26ae-4323-9ca2-7a158bfd9a13",
        "task_id": "287ca258-9e62-44da-b768-a44c7c339922",
        "question": "你好。"
    }
    data = {
        "message_type": "answer",
        "session_id": "ae758c85-26ae-4323-9ca2-7a158bfd9a13",
        "task_id": "287ca258-9e62-44da-b768-a44c7c339922",
        "answer_index": 0,
        "answer": "你好，"
    }
    */
    if (data) {
        if (data['message_type'] === 'question') {
            // 添加问题到当前会话
            if (data.question && data.question.length > 0) {

                // 如果前一个node是问题，且task_id相同，则更新问题内容
                if (currentSession.length > 0 &&
                    currentSession[currentSession.length - 1].type === 'question' &&
                    currentSession[currentSession.length - 1].task_id === data.task_id) {
                    currentSession[currentSession.length - 1].content = data.question; // 更新问题内容
                } else {
                    // 否则，添加新的问题
                    currentSession.push({
                        type: 'question',
                        content: data.question,
                        task_id: data.task_id
                    });
                }
            }

        } else if (data['message_type'] === 'answer') {
            if (data.answer_index === 0) {
                currentSession.push({
                    type: 'answer',
                    content: data.answer,
                    task_id: data.task_id,
                });
            } else {
                // 如果是后续的答案，更新当前会话中的答案
                const lastAnswer = currentSession[currentSession.length - 1];
                if (lastAnswer &&
                    lastAnswer.task_id === data.task_id &&
                    lastAnswer.content !== null && lastAnswer.content.length > 0) {
                    if (lastAnswer.type === 'answer') {
                        lastAnswer.content += data.answer; // 累加答案内容
                    } else {
                        console.warn('Received answer without a matching question in the current session');
                        currentSession.push({
                            type: data.type,
                            content: data.answer,
                            task_id: data.task_id,
                        });
                    }

                } else {
                    console.warn('Received answer without a matching question in the current session');
                }
            }
        }
    }
}


onMounted( async () => {
    // console.log('config', settingsStore.$state)
    await startWebSock();
})

onUnmounted( async () => {
    console.warn('onUnmounted, stop web socket ...')
    stopWebSock();
});

const backAction = async () => {
    const state = await stopAudioCapture();
    if (!state) {
        console.error('Failed to stop audio chat system service');
        return;
    }
    router.replace('/')
}

const stopActionLoading = ref<boolean>(false);
const stopAudioCapture = async () => {
    try {
        stopActionLoading.value = true;

        const response = await fetch(`${base_url}/system/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: null
        });
        if (!response.ok) {

            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('ASR Instance stopped successfully:', data);
        return true;
    } catch (error) {
        console.error('Error stop record :', error);
        return false;
    } finally {
        stopActionLoading.value = false;
    }
}

const micActionLoading = ref<boolean>(false);
const pauseAudioCapture = async () => {
    try {
        micActionLoading.value = true;
        const response = await fetch(`${base_url}/system/pause`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: null
        });
        if (!response.ok) {

            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Mic paused successfully:', data);
        return true;
    } catch (error) {
        console.error('Error pause mic:', error);
        return false;
    } finally {
        micActionLoading.value = false;
    }
}

const resumeAudioCapture = async () => {
    try {
        micActionLoading.value = true;
        const response = await fetch(`${base_url}/system/resume`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: null
        });
        if (!response.ok) {

            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Mic resume successfully:', data);
        return true;
    } catch (error) {
        console.error('Error resume mic:', error);
        return false;
    } finally {
        micActionLoading.value = false;
    }
}


const mic_working = ref<boolean>(true);
const toggleMic = async () => {
    if (mic_working.value) {
        const state = await pauseAudioCapture();
        if (!state) {
            console.error('Failed to stop audio chat system service');
            return;
        }
    } else {
        const state = await resumeAudioCapture();
        if (!state) {
            console.error('Failed to start audio chat system service');
            return;
        }
    }
    mic_working.value = !mic_working.value;
    console.log('mic_state', mic_working.value);
};
const text_state = ref<boolean>(false);
const toggleText = () => {
    text_state.value = !text_state.value;
    console.log('text_state', text_state.value);
};


</script>

<template>
    <div class="chat-wrapper">
        <div class="content">
            <div v-if="!text_state">
                <DynamicBall :isPlaying="mic_working" />
            </div>
            <div v-if="text_state">
                <ChatText :chatContent="currentSession" :isPlaying="mic_working" />
            </div>
        </div>

        <div class="actions">
            <div class="holder">
                <span>&nbsp;</span>
            </div>
            <div class="btns">
                <a-button type="text" style="width:64px; height: 64px;" :loading="micActionLoading" @click="toggleMic">
                    <template #icon>
                        <img :src="mic_working == true ? mic_on : mic_off" width="50" height="50" alt="mic_on" />
                    </template>
                </a-button>
                <a-button type="text" style="width:64px; height: 64px;" @click="toggleText">
                    <template #icon>
                        <img :src="text_state == true ? text_on : text_off" width="50" height="50" alt="text_off" />
                    </template>
                </a-button>
                <a-button type="text" style="width:64px; height: 64px;" :loading="stopActionLoading" @click="backAction">
                    <template #icon>
                        <img :src="close" width="50" height="50" alt="close" />
                    </template>
                </a-button>
            </div>
            <div class="download-wrapper">
                <!-- <a-button type="text" style="width:34px; height: 34px;">
                    <template #icon>
                        <img :src="download" width="20" height="20" alt="settings" />
                    </template>
                </a-button> -->
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.chat-wrapper {
    width: 100%;
    height: 100%;
    background-image: url('@/assets/bg.png');
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-size: cover;
    background-position: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    color: #fff;

    .content {
        width: 100%;
        height: auto;
        display: flex;
        flex-direction: column;
        justify-content: space-around;

        .inner-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 20px;

            .text-box {
                color: #000;
                margin-bottom: 36px;

                .title {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 24px;
                }

                .sub-title {
                    font-size: 15px;
                    margin-top: 10px;
                }
            }

            .btn-box {
                width: 224px;
                height: 80px;
            }
        }
    }

    .actions {
        width: 100%;
        height: 100px;

        display: flex;
        justify-content: space-between;
        align-items: center;

        .holder {
            width: 64px;
            height: 48px;
        }
        .btns {
            width: 450px;
            height: 96px;
            display: flex;
            justify-content: space-around;
            align-items: flex-start;
        }
        .download-wrapper {
            width: 64px;
            height: 64px;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            margin-right: 0;

            img {
                width: 24px;
                height: 24px;
            }
        }
    }
}
</style>
