import axios, {AxiosResponse} from "axios";
import {useCache} from "@/hooks/useCache";
import {toggleError} from '@/hooks/showError'
import router from "@/router";

const { wsCache } = useCache();

export const test_server = '127.0.0.1:8848'
// export const test_server = '59.110.18.232:19001'

axios.defaults.baseURL = import.meta.env.PROD  ?  '/api/v1' : `http://${test_server}/api/v1`;
axios.interceptors.request.use(
    (config: any) => {
        // Do something before request is sent
        const {wsCache} = useCache()
        const token = wsCache.get('token')
        if (token) {
            //@ts-ignore
            config.headers.Authorization = 'Bearer ' + token
        }
        return config;
    }
)
