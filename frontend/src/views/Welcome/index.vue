<script setup lang="ts">

import router from "@/router.ts";
import { useSettingsStore } from "@/stores/config.ts";
import { onMounted, onUnmounted, ref, reactive, computed, watch, h } from "vue";
import { Modal } from 'ant-design-vue';
import { SoundTwoTone, SoundOutlined } from "@ant-design/icons-vue";
import axios from "axios";
import PromptText from "./Components/PromptText.vue";

const base_url = axios.defaults.baseURL

const settingsStore = useSettingsStore()

import setting from "@/assets/setting.png"


onMounted(async () => {
    await fetchASRLanguages();
    await fetchTTSRoles();
});

const chatAction = async () => {
    const state = await startAudioChat();
    if (!state) {
        console.error('Failed to start audio chat system service');

        Modal.error({
            title: 'Error',
            content: 'Failed to start audio chat system service',
        });
        return;
    }
    router.replace('/home')
}
const chatLoading = ref<boolean>(false);

const startAudioChat = async () => {
    try {
        chatLoading.value = true;
        const response = await fetch(`${base_url}/system/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                enable_echo_cancellation: echoCancel.value
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('ASR Instance started successfully:', data);
        return true;
    } catch (error) {
        console.error('Error starting ASR instance:', error);
        return false;
    } finally {
        chatLoading.value = false;
    }
}


const voiceModelOpen = ref<boolean>(false);
const modalLoading = ref<boolean>(false);

const handleVoiceModalCancel = () => {
    voiceModelOpen.value = false;
    role.value = settingsStore.$state.role;
    language.value = settingsStore.$state.language;
};

const handleVoiceModalSubmit = async () => {
    console.log('Selected Language:', language.value);
    console.log('Selected Role:', role.value);
    console.log('Echo Cancel:', echoCancel.value);
    settingsStore.$state.language = language.value;
    settingsStore.$state.role = role.value || '';
    settingsStore.$state.echoCancel = echoCancel.value;

    await pushConfig(settingsStore.$state.role);
};

const pushConfig = async (model_id: string) => {
    try {
        modalLoading.value = true;
        const response = await fetch(`${base_url}/tts/models/load`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "model_id": model_id,
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Config pushed successfully:', data);

        const response2 = await fetch(`${base_url}/asr/instance/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "language": language.value,
            })
        });
        if (!response2.ok) {
            throw new Error(`HTTP error! status: ${response2.status}`);
        }
        const data2 = await response2.json();
        console.log('ASR Language set successfully:', data2);

    } catch (err) {
        console.error('Error pushing config:', err);
        Modal.error({
            title: 'Error',
            content: "Error config: " + JSON.stringify(err),
        });
    } finally {
        modalLoading.value = false;
        voiceModelOpen.value = false;
    }

    console.log('Selected Language:', language.value);
    console.log('Selected Role:', role.value);
}


const language = ref<string>(settingsStore.$state.language || 'zh');
const languages = reactive([]);
const languageOptions = {
    'zh': 'Chinese',
    'en': 'English',
    'auto': 'Auto',
};
const role = ref<string>(settingsStore.$state.role || '');
const roles = reactive([])
const echoCancel = ref<boolean>(settingsStore.$state.echoCancel ?? true);

const radioStyle = reactive({
    display: 'flex',
    height: '40px',
    lineHeight: '40px',
    fontSize: '16px',
    marginBottom: '8px',
});

const filteredRoles = computed(() => {
    const is_chinese = language.value == 'zh';
    return roles.filter(ro => ro['is_chinese_voice'] == is_chinese);
});

watch(
  () => language.value,
  (newLang) => {
    // 语言切换后，自动选中第一个可用角色
    if (filteredRoles.value.length > 0) {
      const current_role_id = settingsStore.$state.role;
      const current_role = filteredRoles.value.find(ro => ro['id'] == current_role_id);
      if (current_role) {
        role.value = current_role_id;
      } else {
        role.value = filteredRoles.value[0]['id'];
      }
    } else {
      role.value = "";
    }
  }
);


const fetchTTSRoles = async () => {
    try {
        const response = await fetch(`${base_url}/tts/models`);
        const data = await response.json()
        if (data && data.models) {
            // @ts-ignore
            roles.splice(0, data.length, ...data.models)
            console.log('Fetched TTS Roles:', roles);

            if (data.current_model_id) {
                role.value = data.current_model_id;
            }
        }
    } catch (error) {
        console.error('Error fetching TTS roles:', error);
    }
};

const fetchASRLanguages = async () => {
    try {
        const response = await fetch(`${base_url}/asr/languages`);
        const data = await response.json();
        if (data && data.languages) {
            // @ts-ignore
            languages.splice(0, languages.length, ...data.languages);
            console.log('Fetched ASR Languages:', data.languages);

            if (data.current_asr_language) {
                language.value = data.current_asr_language;
            }
        }
    } catch (error) {
        console.error('Error fetching ASR languages:', error);
    }
};

const togglePopover = (item: string) => {
    popoverVisible.value = !popoverVisible.value;
    if (item == 'voice') {
        voiceModelOpen.value = true;
    } else if (item == 'prompt') {
        promptModelOpen.value = true;
    }
};

const popoverVisible = ref<boolean>(false);
const promptModelOpen = ref<boolean>(false);

// 音频播放状态管理
const currentPlayingId = ref<string | null>(null);
const currentAudio = ref<HTMLAudioElement | null>(null);

// 修改音频播放逻辑
const playRefAudio = async (id: string, e: Event) => {
    console.log('Playing reference audio for role:', id);

    e.stopPropagation();
    e.preventDefault();

    try {
        // 如果点击的是当前正在播放的音频，则停止播放
        if (currentPlayingId.value === id && currentAudio.value) {
            currentAudio.value.pause();
            currentAudio.value = null;
            currentPlayingId.value = null;
            console.log('Audio stopped');
            return;
        }

        // 如果有其他音频正在播放，先停止它
        if (currentAudio.value) {
            currentAudio.value.pause();
            currentAudio.value = null;
        }

        // 创建新的音频实例
        const audio = new Audio(`${base_url}/tts/models/${id}/reference-audio`);

        // 设置音频事件监听
        audio.addEventListener('ended', () => {
            currentPlayingId.value = null;
            currentAudio.value = null;
        });

        audio.addEventListener('error', (error) => {
            console.error('Audio playback error:', error);
            currentPlayingId.value = null;
            currentAudio.value = null;
            Modal.error({
                title: 'Error',
                content: 'Failed to play reference audio',
            });
        });

        // 开始播放
        await audio.play();
        currentPlayingId.value = id;
        currentAudio.value = audio;
        console.log('Audio played successfully');

    } catch (error) {
        console.error('Error playing audio:', error);
        currentPlayingId.value = null;
        currentAudio.value = null;
        Modal.error({
            title: 'Error',
            content: 'Failed to play reference audio',
        });
    }
};

// 组件卸载时清理音频
onUnmounted(() => {
    if (currentAudio.value) {
        currentAudio.value.pause();
        currentAudio.value = null;
    }
    currentPlayingId.value = null;
});

// 计算属性：判断是否正在播放
const isPlaying = (id: string) => {
    return currentPlayingId.value === id;
};

</script>

<template>
    <div class="welcome-wrapper">
        <div class="content">
            <div class="inner-content">
                <div class="text-box">
                    <div class="title">
                        欢迎使用
                    </div>
                    <div class="sub-title">
                        点击下方按钮开始对话
                    </div>
                </div>
                <div class="btn-box">
                    <a-button @click="chatAction" block :loading="chatLoading" type="primary" size="large">
                        <span>开始对话</span>
                    </a-button>
                </div>
            </div>
        </div>

        <div class="actions">
            <!-- <a-button type="text" @click="toggleSider">sider</a-button> -->

             <a-button v-if="false" type="text" @click="voiceModelOpen = true"
                style="width:44px; height: 44px; margin-right:24px;margin-bottom: 24px;">
                <template #icon>
                    <img :src="setting" width="28" height="28" alt="settings" />
                </template>
            </a-button>
             <a-popover v-if="true" v-model:open="popoverVisible" trigger="click" ok-text="Yes" cancel-text="No" placement="bottomRight">
                <template #content>
                    <div class="custom-popover-list">
                        <div class="custom-popover-item" @click="togglePopover('voice')">
                            选择音色</div>
                        <div class="custom-popover-item" @click="togglePopover('prompt')">Prompt调试</div>
                    </div>
                </template>
                <img :src="setting" alt="item actions" style="width: 28px; height: 28px; margin-right:24px;margin-top: 16px;">
            </a-popover>
        </div>

        <a-modal v-model:open="voiceModelOpen" :title="null" :mask-closable="false" :closable="false" centered>
            <template #footer>
                <a-button key="back" @click="handleVoiceModalCancel">Cancel</a-button>
                <a-button key="submit" type="primary" :loading="modalLoading" @click="handleVoiceModalSubmit">Submit</a-button>
            </template>
            <div class="languages">
                <div class="echo-cancel-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <p style="margin: 0;">Enable Echo Cancellation:</p>
                        <a-switch v-model:checked="echoCancel" />
                    </div>
                </div>
            </div>
            <div class="languages">
                <div class="language-item">
                    <p>Select Language:</p>
                    <a-select v-model:value="language" style="width: 100%;">
                        <a-select-option v-for="lan in languages" :value="lan" :key="lan">
                            {{ languageOptions[lan] }}
                        </a-select-option>
                    </a-select>
                </div>
            </div>
            <div class="languages">
                <div class="role-item">
                    <p>Select voice Role:</p>
                    <a-radio-group size="large" v-model:value="role">
                        <a-radio v-for="r in filteredRoles" :style="radioStyle" :value="r['id']" :key="r['id']">
                            <div style="display: flex; justify-content: space-between; align-items: center; width:450px;">
                            {{ r['character_name'] }}
                            <a-button
                                :key="r['id']"
                                type="text"
                                @click="playRefAudio(r['id'], $event)"
                                class="audio-play-btn"
                                :class="{ 'playing': isPlaying(r['id']) }"
                            >
                                <SoundTwoTone
                                    v-if="isPlaying(r['id'])"
                                    style="font-size: 18px; color: #52c41a;"
                                    class="playing-icon"
                                />
                                <SoundOutlined
                                    v-else
                                    style="font-size: 18px; color: #1890ff;"
                                />
                            </a-button>
                        </div>

                        </a-radio>
                    </a-radio-group>

                </div>
            </div>
        </a-modal>

        <PromptText v-model:open="promptModelOpen" />
    </div>
</template>

<style lang="scss" scoped>

.languages {
    margin-top: 24px;
    margin-bottom: 24px;

    p {
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 8px;
    }
}

.audio-play-btn {
    padding: 0px 8px;
    padding-top:2px;
    border-radius: 4px;
    transition: all 0.2s;
    height: 40px;

    &:hover {
        background-color: #f0f0f0;
    }

    &.playing {
        background-color: #f6ffed;
        border-color: #1890ff;

        .playing-icon {
            animation: pulse 1.5s infinite;
        }
    }
}

@keyframes pulse {
    0% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.7;
        transform: scale(1.1);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}

.btn-groups {
    margin-top: 36px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.custom-popover-list {
    width: 92px;
    margin: 0;
    .custom-popover-item {
        font-size: 14px;
        line-height: 36px;
        font-weight: 500;
        color: #1e1e1e;
        cursor: pointer;
        border-radius: 4px;
        padding: 0 8px;
        margin: 0px -8px;
        transition: background 0.2s;
    }
    .custom-popover-item:hover, .custom-popover-item:focus {
        background: #e5e7eb;
    }
}


.welcome-wrapper {
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
        height: 80vh;
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        margin-top: 64px;

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
        width: 100%;;
        height: 64px;

        display: flex;
        justify-content: flex-end;
    }
}
</style>
