import { defineStore } from 'pinia';


export const useSettingsStore  = defineStore({
    id: 'settings',
    persist: true,
    state: () => {
        return {
            role: '',
            language: 'zh',
            sider_open: true,
            echoCancel: true,
        }
    },
    actions: {
    }
});

