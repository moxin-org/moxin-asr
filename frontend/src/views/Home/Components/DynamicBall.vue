<script setup lang="ts">

import router from "@/router.ts";
import { useSettingsStore } from "@/stores/config.ts";
import { onMounted, ref, watch, defineProps } from "vue";
import { Vue3Lottie, AnimationItem } from 'vue3-lottie'

import ballJson from "@/assets/ball.json";

const props = defineProps({
    isPlaying: {
        type: Boolean,
        default: true
    }
});


onMounted(async () => {
    // console.log('config', settingsStore.$state)
})
const chatAction = () => {
    router.replace('/home')
}

const inputType = ref<string>();
const role = ref<string>();
const onTypeChange = (e: any) => {
    console.log('onTypeChange', e.target.value)
    //   settingsStore.$state.file_type = e.target.value
}

const onRoleChange = (e: any) => {
    console.log('onRoleChange', e.target.value)
    //   settingsStore.$state.role_name = e.target.value
    //   stateStore.changeRole(e.target.value)
    //   console.log('role_name', settingsStore.$state.role_name)
}

const isAnimationPaused = ref<boolean>(true);
const animationSpeed = ref<number>(0); // 动画播放速度，0 表示静止

watch(() => props.isPlaying, (newIsPlayingState) => {
    if (newIsPlayingState) {
        // 如果父组件要求播放
        isAnimationPaused.value = false;
        animationSpeed.value = 1; // 正常速度
    } else {
        // 如果父组件要求暂停
        isAnimationPaused.value = true;
        animationSpeed.value = 0; // 速度为0以暂停
    }
    console.log(`Animation controlled by prop: isPlaying=${newIsPlayingState}, Paused: ${isAnimationPaused.value}, Speed: ${animationSpeed.value}`);
}, { immediate: true });

</script>

<template>
    <div class="ball-wrapper">
        <Vue3Lottie :animationData="ballJson" :autoplay="true" :pauseAnimation="isAnimationPaused"
            :speed="animationSpeed" :height="340" :width="340" />
    </div>
</template>

<style lang="scss" scoped>
.ball-wrapper {
    width: 100%;
    height: calc(100vh - 100px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-around;

}
</style>
