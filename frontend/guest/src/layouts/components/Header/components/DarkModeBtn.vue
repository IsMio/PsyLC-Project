<script setup lang="ts">
import { useDesignStore } from '@/stores';

const designStore = useDesignStore();

const isDark = computed(() => designStore.darkMode === 'dark');
const label = computed(() => (isDark.value ? '浅色' : '深色'));

function applyTheme(mode: 'light' | 'dark') {
  document.documentElement.setAttribute('data-theme', mode);
}

function toggleDarkMode() {
  const nextMode = isDark.value ? 'light' : 'dark';
  designStore.setDarkMode(nextMode);
  applyTheme(nextMode);
}

watch(
  () => designStore.darkMode,
  (mode) => {
    applyTheme(mode === 'dark' ? 'dark' : 'light');
  },
  { immediate: true },
);
</script>

<template>
  <button
    type="button"
    class="dark-mode-btn bg-#191c1f c-#fff font-size-14px rounded-8px flex-center text-overflow p-10px pl-12px pr-12px min-w-49px h-36px cursor-pointer hover:bg-#232629 select-none"
    @click="toggleDarkMode"
  >
    {{ label }}
  </button>
</template>

<style scoped lang="scss">
.dark-mode-btn {
  border: none;
}
</style>
