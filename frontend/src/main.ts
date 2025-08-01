import { createApp } from 'vue'
import Antd from 'ant-design-vue';
import './config/client_config'
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import Vue3Lottie from 'vue3-lottie'
import 'ant-design-vue/dist/reset.css';
import './style.scss'

import App from './App.vue'
import router from './router'


// import * as Sentry from "@sentry/browser";
//
// Sentry.init({
//     dsn: "http://1f5e3e8958a24528b5030068902e177e@127.0.0.1:8543/7",
//     debug: true,
// });

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);



createApp(App)
    .use(pinia)
    .use(router)
    .use(Antd)
    .use(Vue3Lottie)
    .mount('#app')
