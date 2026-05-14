import path from 'node:path';
import process from 'node:process';
import { defineConfig, loadEnv } from 'vite';
import plugins from './.build/plugins';
import { createMockPlugin } from './mock/index.mjs';

// https://vite.dev/config/
export default defineConfig((cnf) => {
  const { mode } = cnf;
  const env = loadEnv(mode, process.cwd());
  const { VITE_APP_ENV } = env;
  const vitePlugins = plugins(cnf);
  const useMock = env.VITE_USE_MOCK === 'true';

  if (useMock)
    vitePlugins.push(createMockPlugin({ base: env.VITE_API_URL || '/dev-api' }));

  return {
    base: VITE_APP_ENV === 'production' ? '/' : '/',
    plugins: vitePlugins,
    server: {
      proxy: useMock
        ? undefined
        : {
            '/dev-api': {
              target: 'http://localhost:8002',
              changeOrigin: true,
              rewrite: path => path.replace(/^\/dev-api/, ''),
            },
          },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    css: {
      // css全局变量使用，@/styles/variable.scss文件
      preprocessorOptions: {
        scss: {
          additionalData: '@use "@/styles/var.scss" as *;',
        },
      },
    },
  };
});
