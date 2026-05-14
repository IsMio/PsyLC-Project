import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, logout, getCurrentUser } from '../../api/auth'

interface UserState {
  token: string | null
  userInfo: any
  roles: string[]
  permissions: string[]
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<any>(null)
  const roles = ref<string[]>([])
  const permissions = ref<string[]>([])

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => roles.value.includes('admin'))

  const normalizeUserInfo = (info: any) => ({
    ...info,
    userId: info?.userId || info?.id || '',
    nickName: info?.nickName || info?.display_name || info?.username || '',
    display_name: info?.display_name || info?.nickName || info?.username || ''
  })

  const loginAction = async (username: string, password: string) => {
    try {
      const response = await login({ username, password })
      const { token: newToken, userInfo: rawInfo } = response.data
      const info = normalizeUserInfo(rawInfo)
      token.value = newToken
      userInfo.value = info
      roles.value = info.roles || []
      permissions.value = info.rolePermission || []
      localStorage.setItem('token', newToken)
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logoutAction = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      token.value = null
      userInfo.value = null
      roles.value = []
      permissions.value = []
      localStorage.removeItem('token')
    }
  }

  const getUserInfo = async () => {
    try {
      const response = await getCurrentUser()
      const info = normalizeUserInfo(response.data.userInfo)
      userInfo.value = info
      roles.value = info.roles || []
      permissions.value = info.rolePermission || []
      return info
    } catch (error) {
      console.error('Get user info failed:', error)
      token.value = null
      userInfo.value = null
      roles.value = []
      permissions.value = []
      localStorage.removeItem('token')
      return null
    }
  }

  return {
    token,
    userInfo,
    roles,
    permissions,
    isLoggedIn,
    isAdmin,
    loginAction,
    logoutAction,
    getUserInfo
  }
})
