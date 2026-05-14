<template>
  <div class="admin-layout">
    <a-layout class="layout-shell">
      <a-layout-sider
        v-model:collapsed="collapsed"
        :trigger="null"
        collapsible
        width="248"
        class="layout-sider"
      >
        <div class="brand">
          <div class="brand-mark">P</div>
          <div v-if="!collapsed" class="brand-copy">
            <strong>PsyLC Admin</strong>
            <span>运营控制台</span>
          </div>
        </div>

        <a-menu
          mode="inline"
          :selected-keys="selectedKeys"
          :open-keys="openKeys"
          :items="menuItems"
          class="side-menu"
          @click="handleMenuClick"
          @openChange="handleOpenChange"
        />
      </a-layout-sider>

      <a-layout>
        <a-layout-header class="layout-header">
          <div class="header-left">
            <a-button type="text" class="trigger-btn" @click="collapsed = !collapsed">
              <MenuOutlined />
            </a-button>
            <div>
              <div class="page-title">{{ currentTitle }}</div>
              <div class="page-subtitle">{{ currentDateText }}</div>
            </div>
          </div>

          <div class="header-right">
            <a-tooltip :title="themeStore.isDark ? '切换为浅色模式' : '切换为深色模式'">
              <a-button type="text" class="theme-btn" @click="themeStore.toggleTheme()">
                <BulbOutlined v-if="!themeStore.isDark" />
                <BgColorsOutlined v-else />
              </a-button>
            </a-tooltip>
            <a-avatar :src="userInfo?.avatar" :size="40">
              {{ userInitial }}
            </a-avatar>
            <a-dropdown>
              <a class="user-link" @click.prevent>
                <span>{{ displayName }}</span>
                <DownOutlined />
              </a>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="theme" disabled>
                    {{ themeStore.isDark ? '当前为深色模式' : '当前为浅色模式' }}
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="logout" @click="handleLogout">
                    <LogoutOutlined />
                    <span>退出登录</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </a-layout-header>

        <a-layout-content class="layout-content">
          <router-view />
        </a-layout-content>
      </a-layout>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { ItemType } from 'ant-design-vue'
import { useUserStore } from '../store/modules/user'
import { useThemeStore } from '../store/modules/theme'
import {
  BgColorsOutlined,
  BookOutlined,
  BulbOutlined,
  DashboardOutlined,
  DownOutlined,
  LogoutOutlined,
  MenuOutlined,
  MonitorOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])

const iconMap = {
  Dashboard: DashboardOutlined,
  User: UserOutlined,
  Book: BookOutlined,
  Monitor: MonitorOutlined
} as const

const rootRoutes = computed(() =>
  router.options.routes.filter(
    (item) => !['/login', '/403'].includes(item.path) && (!item.meta?.requiresAdmin || userStore.isAdmin)
  )
)

const menuItems = computed<ItemType[]>(() => {
  return rootRoutes.value
    .map((item) => {
      if (!item.children?.length) {
        return null
      }

      if (item.path === '/') {
        const child = item.children[0]
        return {
          key: '/dashboard',
          icon: renderIcon(item.children[0]?.meta?.icon as string | undefined),
          label: child.meta?.title as string
        }
      }

        return {
          key: item.path,
          icon: renderIcon(item.meta?.icon as string | undefined),
          label: item.meta?.title as string,
          children: item.children
          .filter((child) => !child.meta?.hidden && (!child.meta?.requiresAdmin || userStore.isAdmin))
          .map((child) => ({
            key: `${item.path}/${child.path}`,
            label: child.meta?.title as string
          }))
        }
    })
    .filter(Boolean) as ItemType[]
})

const userInfo = computed(() => userStore.userInfo)
const displayName = computed(() => userInfo.value?.display_name || userInfo.value?.nickName || userInfo.value?.username || 'Admin')
const userInitial = computed(() => String(displayName.value).slice(0, 1).toUpperCase())
const currentTitle = computed(() => (route.meta.title as string) || '控制台')
const currentDateText = computed(() => {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  }).format(new Date())
})

const renderIcon = (iconName?: string) => {
  const Icon = iconMap[iconName as keyof typeof iconMap] || DashboardOutlined
  return h(Icon)
}

const updateMenuState = () => {
  selectedKeys.value = [route.path]

  if (route.path === '/dashboard') {
    openKeys.value = []
    return
  }

  const parent = `/${route.path.split('/')[1]}`
  openKeys.value = [parent]
}

const handleMenuClick = ({ key }: { key: string }) => {
  router.push(key)
}

const handleOpenChange = (keys: string[]) => {
  openKeys.value = keys.slice(-1)
}

const handleLogout = async () => {
  await userStore.logoutAction()
  router.push('/login')
}

watch(() => route.path, updateMenuState, { immediate: true })

onMounted(async () => {
  if (!userStore.userInfo) {
    await userStore.getUserInfo()
  }
})
</script>

<style scoped>
.admin-layout,
.layout-shell {
  min-height: 100vh;
}

.layout-sider {
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.14), transparent 36%),
    linear-gradient(180deg, var(--sider-bg-top) 0%, var(--sider-bg-bottom) 100%);
  box-shadow: 16px 0 32px rgba(9, 23, 44, 0.18);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 76px;
  padding: 18px 20px 12px;
  color: #f3f7ff;
}

.brand-mark {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 14px;
  font-size: 20px;
  font-weight: 700;
  color: #17325c;
  background: linear-gradient(135deg, #f7d794 0%, #fef3c7 100%);
}

.brand-copy {
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  font-size: 16px;
  letter-spacing: 0.04em;
}

.brand-copy span {
  font-size: 12px;
  color: rgba(243, 247, 255, 0.72);
}

:deep(.side-menu) {
  background: transparent;
  color: rgba(243, 247, 255, 0.82);
  border-inline-end: 0;
}

:deep(.side-menu .ant-menu-item),
:deep(.side-menu .ant-menu-submenu-title) {
  width: calc(100% - 16px);
  margin-inline: 8px;
  border-radius: 14px;
}

:deep(.side-menu .ant-menu-item-selected) {
  color: #17325c;
  background: linear-gradient(135deg, #f7d794 0%, #f4c56e 100%);
}

:deep(.side-menu .ant-menu-submenu-selected > .ant-menu-submenu-title) {
  color: #ffffff;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 84px;
  padding: 0 28px;
  background: var(--header-surface);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border-soft);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.trigger-btn,
.theme-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  color: var(--text-main);
  background: var(--control-surface);
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
}

.user-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-main);
  font-weight: 600;
}

.layout-content {
  padding: 24px;
}

@media (max-width: 900px) {
  .layout-header {
    height: auto;
    padding: 16px;
    gap: 16px;
    align-items: flex-start;
    flex-direction: column;
  }

  .layout-content {
    padding: 16px;
  }
}
</style>
