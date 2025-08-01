<script setup lang="ts">

import router from "@/router.ts";
import { useSettingsStore } from "@/stores/config.ts";
import {onMounted, ref} from "vue";
import {SettingTwoTone} from "@ant-design/icons-vue";

const settingsStore = useSettingsStore()

onMounted(() => {
  console.log('config', settingsStore.$state)
})
const backAction = () => {
  router.replace('/')
}

// const inputType = ref<string>(settingsStore.$state.file_type);
// const role = ref<string>(settingsStore.$state.role_name);
// const onTypeChange = (e: any) => {
//   console.log('onTypeChange', e.target.value)
//   settingsStore.$state.file_type = e.target.value
// }

// const onRoleChange = (e: any) => {
//   console.log('onRoleChange', e.target.value)
//   settingsStore.$state.role_name = e.target.value
//   stateStore.changeRole(e.target.value)
//   console.log('role_name', settingsStore.$state.role_name)
// }


</script>

<template>
  <div class="content-wrapper">
    <a-result style="width: 100%;" title="Settings">
      <!-- <template #icon>
        <img
            alt="logo"
            src="/logo.webp"
            style="width: 128px; border-radius: 24px;"
        />
      </template>
      <template #extra>
        <div class="content-box">
          <a-form layout="vertical">
            <a-form-item
                         label="Choose your input type:"
                         name="inputType"
            >
              <a-radio-group v-model:value="inputType" @change="onTypeChange">
                <a-radio :value="'file'">Audio File</a-radio>
                <a-radio :value="'audio'">Speak</a-radio>
              </a-radio-group>
            </a-form-item>

            <a-form-item
                         label="Choose your desire role:"
                         name="role"
            >
              <a-radio-group  v-model:value="role" @change="onRoleChange">
                <a-radio :value="'trump'">Trump</a-radio>
                <a-radio :value="'ellen'">Ellen</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-form>
        </div>

        <a-button @click="backAction" type="primary">Back</a-button>
      </template> -->

    </a-result>
  </div>
</template>

<style lang="scss" scoped>

.content-wrapper {
  text-align: left;
  max-width: 800px;
  min-width: 320px;
  margin-bottom: 64px;
  min-height: calc(100vh - 438px);

  .content-box {
    padding: 24px;
    height: 240px;
    background-color: #e8e8e8;
    border-radius: 16px;
    width: 50%;
    margin: 48px auto;
    min-width: 300px;
  }

  .video-box {
    max-width: 800px;
    min-width: 320px;
    width: 90vw;
    height: auto;
  }
}

</style>
