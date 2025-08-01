<script setup lang="ts">
import { ref, watch } from "vue";
import { Modal } from 'ant-design-vue';
import axios from "axios";

const base_url = axios.defaults.baseURL;

// Props
const props = defineProps({
    open: {
        type: Boolean,
        default: false
    }
});

// Emits
const emit = defineEmits(['update:open']);

// 默认提示词
const default_prompt_en = ref<string>('');
const default_prompt_zh = ref<string>('');

// 响应式数据
const current_prompt_en = ref<string>('');
const current_prompt_zh = ref<string>('');

const modalLoading = ref<boolean>(false);
const languageSegment = ref<string>('zh');

const fetchDefaultPrompt = async () => {
    try {
        const response = await fetch(`${base_url}/settings/settings/prompts/default`);
        const data = await response.json();

        if (data) {
            // @ts-ignore
            default_prompt_en.value = data.english_prompt;
            default_prompt_zh.value = data.chinese_prompt;
        }
    } catch (error) {
        console.error('Error fetching default prompt:', error);
    }
};

const fetchCurrentPrompt = async () => {
    try {
        const response = await fetch(`${base_url}/settings/settings/prompts`);
        const data = await response.json();

        if (data) {
            // @ts-ignore
            current_prompt_en.value = data.english_prompt;
            current_prompt_zh.value = data.chinese_prompt;
        }
    } catch (error) {
        console.error('Error fetching current prompt:', error);
    }
};

const updateCurrentPrompt = async () => {
    try {
        modalLoading.value = true;
        const response = await fetch(`${base_url}/settings/settings/prompts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chinese_prompt: current_prompt_zh.value,
                english_prompt: current_prompt_en.value
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Current prompt updated successfully:', data);
    } catch (error) {
        console.error('Error updating current prompt:', error);
    } finally {
        modalLoading.value = false;
    }
};

const resetDefaultPrompt = async () => {
    try {
        modalLoading.value = true;
        const response = await fetch(`${base_url}/settings/settings/prompts`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Default prompt reset successfully:', data);
        current_prompt_en.value = default_prompt_en.value;
        current_prompt_zh.value = default_prompt_zh.value;
    } catch (error) {
        console.error('Error resetting default prompt:', error);
    } finally {
        modalLoading.value = false;
    }
};


// 方法
const handleCancel = async () => {
    await fetchCurrentPrompt();
    emit('update:open', false);
};

const handleSubmit = async () => {
    await updateCurrentPrompt();
    await fetchCurrentPrompt();
    emit('update:open', false);
};

const handleResetPrompt = async (language: string) => {
    await fetchDefaultPrompt();
    if (language == 'en') {
        current_prompt_en.value = default_prompt_en.value;
    } else {
        current_prompt_zh.value = default_prompt_zh.value;
    }
};

// 监听open变化，初始化prompt值
watch(() => props.open, (newOpen) => {
    if (newOpen) {
        fetchCurrentPrompt();
        fetchDefaultPrompt();
    }
});

</script>

<template>
    <a-modal
        key="prompt-text-modal"
        v-model:open="props.open"
        :title="null"
        :mask-closable="false"
        :closable="false"
        centered
        @update:open="(val: boolean) => emit('update:open', val)"
    >
        <template #footer>
            <div class="btn-groups">
                <div class="btn-group">
                    <a-button key="back" @click="handleCancel">Cancel</a-button>
                    <a-button key="submit" type="primary" :loading="modalLoading" @click="handleSubmit">Submit</a-button>
                </div>
            </div>
        </template>

        <div class="prompt-content">
            <div class="prompt-title">
                <p>Prompt Debug</p>
            </div>
            <a-radio-group button-style="solid" size="medium" v-model:value="languageSegment" class="language-segment">
                <a-radio-button value="zh">Chinese</a-radio-button>
                <a-radio-button value="en">English</a-radio-button>
            </a-radio-group>
            <div v-if="languageSegment == 'en'" class="prompt-item">
                <a-textarea
                    v-model:value="current_prompt_en"
                    :placeholder="default_prompt_en"
                    :auto-size="{ minRows: 10, maxRows: 20 }"
                    show-count
                    :maxlength="2000"
                    allow-clear
                    class="prompt-textarea"
                />
                <a-button size="small" key="reset-en" @click="handleResetPrompt('en')" style="margin-top: 16px;">Reset</a-button>
            </div>
            <div v-if="languageSegment == 'zh'" class="prompt-item">
                <a-textarea
                    v-model:value="current_prompt_zh"
                    :placeholder="default_prompt_zh"
                    :auto-size="{ minRows: 10, maxRows: 20 }"
                    show-count
                    :maxlength="2000"
                    allow-clear
                    class="prompt-textarea"
                />
                <a-button size="small" key="reset-zh" @click="handleResetPrompt('zh')" style="margin-top: 16px;">Reset</a-button>
            </div>
        </div>
    </a-modal>
</template>

<style lang="scss" scoped>
.btn-groups {
    margin-top: 36px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
}

.prompt-title {
    p {
        margin: 0;
        font-size: 16px;
        font-weight: 500;
    }
}

.prompt-content {
    margin-top: 16px;

    .prompt-title {
        margin-bottom: 24px;
        font-size: 22px;
        font-weight: 500;
        text-align: center;
    }

    .language-segment {
        display: flex;
        justify-content: center;
        margin-bottom: 16px;
    }

    .prompt-item {
        margin-top: 16px;
    }
}
</style>
