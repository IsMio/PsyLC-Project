import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'theme-mode'

const applyTheme = (mode: ThemeMode) => {
  document.documentElement.setAttribute('data-theme', mode)
}

export const useThemeStore = defineStore('theme', () => {
  const themeMode = ref<ThemeMode>((localStorage.getItem(STORAGE_KEY) as ThemeMode) || 'light')

  const isDark = computed(() => themeMode.value === 'dark')

  const setTheme = (mode: ThemeMode) => {
    themeMode.value = mode
    localStorage.setItem(STORAGE_KEY, mode)
    applyTheme(mode)
  }

  const toggleTheme = () => {
    setTheme(isDark.value ? 'light' : 'dark')
  }

  const initTheme = () => {
    applyTheme(themeMode.value)
  }

  return {
    themeMode,
    isDark,
    setTheme,
    toggleTheme,
    initTheme
  }
})

