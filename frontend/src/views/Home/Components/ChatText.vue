<script setup lang="ts">

import router from "@/router.ts";
import { useSettingsStore } from "@/stores/config.ts";
import { onMounted, ref, nextTick, watch, defineProps } from "vue";

const props = defineProps({
    isPlaying: {
        type: Boolean,
        default: true
    },
    chatContent: {
        type: [Object],
        default: []
    }
});

const contentListRef = ref(null);
// 自动滚动到底部的函数
const scrollToBottom = () => {
    nextTick(() => {
        if (contentListRef.value) {
            // @ts-ignore
            contentListRef.value.scrollTop = contentListRef.value.scrollHeight + 24;
        }
    });
};

// 监听 chatContent 的变化，自动滚动到底部, 具体list里面的某一条内容的长度改变了，或者list的长度改变了，也需要刷新
watch(() => props.chatContent, (newVal, oldVal) => {
    // console.log('chatContent , auto scroll to bottom.....', newVal);
    scrollToBottom();
}, { deep: true });
</script>

<template>
    <div ref="contentListRef" class="talk-wrapper">
        <div v-for="node, index in chatContent" :class="[node.type == 'answer' ? 'cont-left' : 'cont-right']" :key="index">
            <div :class="[node.type == 'answer' ? 'text-left' : 'text-right']">
                {{ node.content }}
            </div>
        </div>

        <!-- <div class="cont-left">
            <div>
                <a-avatar size="large" :style="{ backgroundColor: 'green', verticalAlign: 'middle' }" :gap="1">
                    {{ 'AI' }}
                </a-avatar>
            </div>
            <div class="text-left">
                你好，今天的天气怎么样？
                早上好，今天的天气不错，适合出去走走。
            </div>
        </div>
        <div class="cont-right">
            <div class="text-right">
                是的，今天天气很好，阳光明媚。
            </div>
            <div>
                <a-avatar size="large" :style="{ backgroundColor: 'orange', verticalAlign: 'middle' }" :gap="1">
                    {{ 'U' }}
                </a-avatar>
            </div>
        </div> -->

    </div>
</template>

<style lang="scss" scoped>
.talk-wrapper {
    width: auto;
    height: calc(100vh - 100px);
    overflow-y: scroll;
    padding: 20px 240px 0 240px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;

    .cont-left {
        width: 100%;

        margin: 24px 0;
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        .text-left {
            color: #222;
            font-size: 16px;
            font-weight: 400;
            text-align: left;
            line-height: 2;
            margin-left: 12px;
            margin-top: 6px;
        }
    }

    .cont-right {
        width: 100%;
        margin: 24px 0;
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;

        .text-right {
            color: #444;
            font-size: 16px;
            font-weight: 400;
            text-align: end;
            line-height: 2;
            margin-right: 12px;
            background: #ccc;
            border-radius: 8px;
            border-top-right-radius: 0;
            padding: 8px;
        }
    }
}
</style>
