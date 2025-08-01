<script lang="ts" setup>
import router from "@/router.ts";
import {watch, ref, onMounted, onUnmounted} from "vue";

import MinimizeIcon from "@/assets/icons/yellow.png"
import MaximizeIcon from "@/assets/icons/green.png"
import CloseIcon from "@/assets/icons/red.png"
import MinFocusIcon from "@/assets/icons/min.png"
import MaxFocusIcon from "@/assets/icons/max.png"
import CloseFocusIcon from "@/assets/icons/close.png"


// 修改electron的导入方式
let electronAPI: any = null;

// 检查是否在Electron环境中
// @ts-ignore
if (typeof window !== 'undefined' && window.electronAPI) {
    // @ts-ignore
    electronAPI = window.electronAPI;
}

// 添加窗口控制函数 - 使用contextBridge API
const minimizeWindow = () => {
    if (electronAPI) {
        // 通过preload脚本发送事件
        // @ts-ignore
        window.electronAPI?.minimizeWindow?.();
    } else {
        console.warn('Electron API not available');
    }
}

const maximizeWindow = () => {
    if (electronAPI) {
        // @ts-ignore
        window.electronAPI?.maximizeWindow?.();
    } else {
        console.warn('Electron API not available');
    }
}

const closeWindow = () => {
    if (electronAPI) {
        // @ts-ignore
        window.electronAPI?.closeWindow?.();
    } else {
        console.warn('Electron API not available');
    }
}

</script>
<template>
 <div class="header-nav">
  <div class="window-controls">
      <a-button type="link" size="small" @click="closeWindow" style="width:24px; height: 24px; padding: 0;">
          <template #icon>
              <img class="close-icon default" :src="CloseIcon" alt="close" style="width: 12px; height: 12px;">
              <img class="close-icon focus" :src="CloseFocusIcon" alt="close-focus"
                  style="width: 12px; height: 12px;">
          </template>
      </a-button>
      <a-button type="link" size="small" @click="minimizeWindow"
          style="width:24px; height: 24px; padding: 0;">
          <template #icon>
              <img class="close-icon default" :src="MinimizeIcon" alt="min" style="width: 12px; height: 12px;">
              <img class="close-icon focus" :src="MinFocusIcon" alt="min-focus"
                  style="width: 12px; height: 12px;">
          </template>
      </a-button>
      <a-button type="link" size="small" @click="maximizeWindow"
          style="width:24px; height: 24px; padding: 0;">
          <template #icon>
              <img class="close-icon default" :src="MaximizeIcon" alt="max" style="width: 12px; height: 12px;">
              <img class="close-icon focus" :src="MaxFocusIcon" alt="max-focus"
                  style="width: 12px; height: 12px;">
          </template>
      </a-button>
  </div>
 </div>
</template>
<style scoped lang="scss">
.header-nav {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  width: 100vw;
  height: 40px;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 99;
  -webkit-app-region: drag;
  /* 整个header区域可拖拽 */
  cursor: move;

  /* 确保所有交互元素不可拖拽 */
  .window-controls,
  button,
  .ant-input-search,
  img,
  .anticon {
      -webkit-app-region: no-drag;
      cursor: pointer;
  }

  .window-controls {
      top: 0;
      right: 0;
      display: flex;
      z-index: 1000;
      margin-left: 12px;

      .window-control-btn {
          width: 46px;
          height: 32px;
          border: none;
          background: transparent;
          color: #666;
          font-size: 16px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background-color 0.2s;

          &:hover {
              background-color: rgba(0, 0, 0, 0.1);
          }

          &.close:hover {
              background-color: #e81123;
              color: white;
          }
      }

      .close-icon.focus {
          display: none;
      }

      &:hover .close-icon.default,
      &:focus-within .close-icon.default {
          display: none;
      }

      &:hover .close-icon.focus,
      &:focus-within .close-icon.focus {
          display: inline;
      }
  }
}

</style>
