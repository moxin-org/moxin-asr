import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { viteStaticCopy } from 'vite-plugin-static-copy'

const absPath = (fp: string): string => {
  return resolve(__dirname, fp)
}
// https://vitejs.dev/config/
export default defineConfig({
  define: {
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'true'
  },
  base: "./",
  build: {
    outDir: 'www',
  },
  plugins: [vue({
    script: {
      defineModel: true
    }
  }),
    // viteStaticCopy({
    //   targets: [
    //     {
    //       src: 'node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js',
    //       dest: './assets/'
    //     },
    //     {
    //       src: 'node_modules/@ricky0123/vad-web/dist/silero_vad.onnx',
    //       dest: './assets/'
    //     },
    //     {
    //       src: 'node_modules/onnxruntime-web/dist/*.wasm',
    //       dest: './assets/'
    //     },
    //     {
    //       src: 'node_modules/onnxruntime-web/dist/*.mjs',
    //       dest: './assets/'
    //     }
    //   ]
    // })
  ],
  assetsInclude: [
      "**/*.txt",
  ],
  resolve: {
    alias: {
      // @ is an alias to /src
      '@': absPath('src'),
    }
  }
})
