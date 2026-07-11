import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devProxyTarget = env.VITE_DEV_PROXY_TARGET?.trim()

  return {
    base: env.VITE_BASE_PATH || '/',
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      ...(devProxyTarget
        ? {
            proxy: {
              '/api': {
                target: devProxyTarget,
                changeOrigin: true,
              },
            },
          }
        : {}),
    },
  }
})
