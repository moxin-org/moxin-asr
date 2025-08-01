<template>
  <Header/>
  <router-view class="content" />
  <!-- <Footer/> -->

  <!-- <a-layout>
    <a-layout-sider :style="siderStyle" width="300" :collapsed-width="0" :collapsed="!sider_open" >
      Sider
      <a-button @click="toggleSider">close</a-button>
    </a-layout-sider>
    <a-layout>
      <router-view class="content" />
    </a-layout>
  </a-layout> -->

</template>

<script setup lang="ts">
import Header from "@/views/Header.vue";
import Footer from "@/views/Footer.vue";

// import * as api from "@/client";
import { onBeforeMount, onMounted, watch, CSSProperties, ref} from "vue";
import {useSettingsStore} from "@/stores/config.ts";

import axios from "axios";
import {getRandomNumInt} from "@/utils/size.ts";

const base_url = axios.defaults.baseURL

const settingsStore = useSettingsStore();

const sider_open = ref(settingsStore.$state.sider_open);
const siderStyle: CSSProperties = {
  textAlign: 'center',
  lineHeight: '90px',
  color: '#fff',
  backgroundColor: '#3ba0e9',
};

watch(() => settingsStore.$state.sider_open, (newVal) => {
  sider_open.value = newVal;
  console.log('sider open changed: ', sider_open.value);
});

const toggleSider = () => {
  sider_open.value = !sider_open.value;
  settingsStore.$patch({sider_open: sider_open.value});
  console.log('sider open: ', sider_open.value);
}

// const registerSession = async () => {
//   console.log('register ...')
//   const role = settingsStore.$state.role_name

//   const response = await fetch(`${base_url}/register?role=${role}`)
//   const res = await response.json()
//   console.log('res: ', res)
//   return res['session_id']
// }

// watch(() => settingsStore.$state.role_name, async (role_name: any) => {
//   console.log('>>>>> role updated', role_name)
//   let session_id = await registerSession()
//   if (!session_id) {
//     console.log('register session failed')
//     session_id = getRandomNumInt(100000, 999999)
//   }
//   // @ts-ignore
//   sessionsStore.$patch({current_session_id: session_id + ''})
//   console.log('session id: ', sessionsStore.$state.current_session_id)
// })

onMounted(async () => {
  // console.log('app mounted', settingsStore.$state)

  // let session_id = await registerSession()
  // if (!session_id) {
  //   console.log('register session failed')
  //   session_id = getRandomNumInt(100000, 999999)
  // }
  // // @ts-ignore
  // sessionsStore.$patch({current_session_id: session_id + ''})
  // console.log('session id: ', sessionsStore.$state.current_session_id)
})

</script>

<style scoped>
.content {
  background-color: white;
  /* max-width: 1280px;
  min-height: 720px; */
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
}
</style>
