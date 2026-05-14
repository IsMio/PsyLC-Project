import type { LoginUser } from '@/api/auth/types';
import { defineStore } from 'pinia';
import { useRouter } from 'vue-router';

export const useUserStore = defineStore(
  'user',
  () => {
    const token = ref<string>();
    const router = useRouter();
    const setToken = (value: string) => {
      token.value = value;
    };
    const clearToken = () => {
      token.value = void 0;
    };

    const userInfo = ref<LoginUser>();
    const setUserInfo = (value: LoginUser) => {
      userInfo.value = value;
    };
    const clearUserInfo = () => {
      userInfo.value = void 0;
    };

    const isLoginDialogVisible = ref(false);

    const logout = async () => {
      clearToken();
      clearUserInfo();
      isLoginDialogVisible.value = false;
      // Clear persisted user cache to avoid restoring stale auth data.
      localStorage.removeItem('user');
      localStorage.removeItem('pinia-user');
      localStorage.removeItem('token');
      sessionStorage.removeItem('user');
      sessionStorage.removeItem('pinia-user');
      sessionStorage.removeItem('token');
      router.replace({ name: 'chat' });
    };

    const openLoginDialog = () => {
      isLoginDialogVisible.value = true;
    };

    const closeLoginDialog = () => {
      isLoginDialogVisible.value = false;
    };

    return {
      token,
      setToken,
      clearToken,
      userInfo,
      setUserInfo,
      clearUserInfo,
      logout,
      isLoginDialogVisible,
      openLoginDialog,
      closeLoginDialog,
    };
  },
  {
    persist: true,
  },
);
