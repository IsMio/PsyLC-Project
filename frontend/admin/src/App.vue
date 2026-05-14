<template>
  <a-config-provider :theme="antdThemeConfig">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { theme as antdTheme } from 'ant-design-vue'
import { useThemeStore } from './store/modules/theme'

const themeStore = useThemeStore()

const antdThemeConfig = computed(() => ({
  algorithm: themeStore.isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
  token: {
    colorPrimary: '#d7a54a',
    borderRadius: 16,
    fontFamily: "'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif"
  }
}))
</script>

