import { defineStore } from 'pinia';

export const useMeasureStore  = defineStore({
    id: 'measure_store',
    persist: false,
    state: () => {
        return {
            first_request_time: 0,
            first_response_time: 0,
        }
    },
    actions: {
    }
});

