import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosRequestHeaders,
  AxiosResponse,
  AxiosError
} from 'axios'

import { notification } from 'ant-design-vue';

import qs from 'qs'

import { config } from '@/config/axios/config'

const { result_code, base_url } = config

// export const PATH_URL = base_url[import.meta.env.VITE_API_BASEPATH]

// export const PATH_URL = 'localhost:8000/'
export const PATH_URL = '/'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: PATH_URL, // api 的 base_url
  timeout: config.request_timeout // 请求超时时间
})

// request拦截器
service.interceptors.request.use(
  (config: any ) => {
    if (
      config.method === 'post' &&
      (config.headers as AxiosRequestHeaders)['Content-Type'] ===
        'application/x-www-form-urlencoded'
    ) {
      config.data = qs.stringify(config.data)
    }
    // get参数编码
    if (config.method === 'get' && config.params) {
      let url = config.url as string
      url += '?'
      const keys = Object.keys(config.params)
      for (const key of keys) {
        if (config.params[key] !== void 0 && config.params[key] !== null) {
          url += `${key}=${encodeURIComponent(config.params[key])}&`
        }
      }
      url = url.substring(0, url.length - 1)
      config.params = {}
      config.url = url
    }
    return config
  },
  (error: AxiosError) => {
    // Do something with request error
    Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response: any) => {
    if (response.data.code === result_code) {
      return response.data
    } else {
      notification.error(response.data.message)
    }
  },
  (error: AxiosError) => {
    console.log('err' + error) // for debug
    notification.error(error)
    return Promise.reject(error)
  }
)

export { service }
