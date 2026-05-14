import type { HookFetchPlugin } from 'hook-fetch';
import { ElMessage } from 'element-plus';
import hookFetch from 'hook-fetch';
import { sseTextDecoderPlugin } from 'hook-fetch/plugins';
import router from '@/routers';
import { useUserStore } from '@/stores';

interface BaseResponse {
  code: number;
  data: never;
  msg: string;
  rows: never;
}

export const request = hookFetch.create<BaseResponse, 'data' | 'rows'>({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  plugins: [sseTextDecoderPlugin({ json: true, prefix: 'data:' })],
});

function jwtPlugin(): HookFetchPlugin<BaseResponse> {
  const userStore = useUserStore();
  let reloginTriggered = false;

  const forceRelogin = () => {
    if (reloginTriggered)
      return;
    reloginTriggered = true;
    userStore.logout();
    if (!userStore.isLoginDialogVisible) {
      userStore.openLoginDialog();
      ElMessage.error('登录状态已失效，请重新登录');
    }
    setTimeout(() => {
      reloginTriggered = false;
    }, 300);
  };

  const getStatus = (payload: any): number | undefined => {
    return payload?.status ?? payload?.response?.status ?? payload?.raw?.status;
  };

  return {
    name: 'jwt',
    beforeRequest: async (config) => {
      config.headers = new Headers(config.headers);
      config.headers.set('authorization', `Bearer ${userStore.token}`);
      return config;
    },
    afterResponse: async (response) => {
      const httpStatus = getStatus(response);
      if (httpStatus === 401 || response.result?.code === 401) {
        forceRelogin();
        return Promise.reject(response);
      }

      if (response.result?.code === 200) {
        return response;
      }

      if (response.result?.code === 403) {
        router.replace({
          name: '403',
        });
        ElMessage.error(response.result?.msg);
        return Promise.reject(response);
      }

      ElMessage.error(response.result?.msg);
      return Promise.reject(response);
    },
    onError: async (error) => {
      const httpStatus = getStatus(error);
      console.error('Request error:', error);
      if (httpStatus === 401) {
        forceRelogin();
      }
      return error;
    },
  };
}

request.use(jwtPlugin());

export const post = request.post;

export const get = request.get;

export const put = request.put;

export const del = request.delete;

export default request;
