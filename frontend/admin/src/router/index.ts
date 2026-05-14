import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import Layout from '../layout/index.vue'
import pinia from '../store'
import { useUserStore } from '../store/modules/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/index.vue'),
    meta: { hidden: true, title: '登录' }
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('../views/error/403.vue'),
    meta: { hidden: true, title: '无权限' }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'Dashboard', requiresAdmin: true }
      }
    ]
  },
  {
    path: '/user',
    component: Layout,
    redirect: '/user/list',
    meta: { title: '用户管理', icon: 'User', requiresAdmin: true },
    children: [
      {
        path: 'list',
        name: 'UserList',
        component: () => import('../views/user/index.vue'),
        meta: { title: '用户列表', requiresAdmin: true }
      }
    ]
  },
  {
    path: '/knowledge',
    component: Layout,
    redirect: '/knowledge/list',
    meta: { title: '知识库管理', icon: 'Book', requiresAdmin: true },
    children: [
      {
        path: 'list',
        name: 'KnowledgeList',
        component: () => import('../views/knowledge/index.vue'),
        meta: { title: '知识库列表', requiresAdmin: true }
      },
      {
        path: 'create',
        name: 'KnowledgeCreate',
        component: () => import('../views/knowledge/create.vue'),
        meta: { title: '新建知识库', hidden: true, requiresAdmin: true }
      },
      {
        path: 'edit/:id',
        name: 'KnowledgeEdit',
        component: () => import('../views/knowledge/edit.vue'),
        meta: { title: '编辑知识库', hidden: true, requiresAdmin: true }
      },
      {
        path: 'jobs/:id',
        name: 'KnowledgeJobDetail',
        component: () => import('../views/knowledge/job-detail.vue'),
        meta: { title: '任务详情', hidden: true, requiresAdmin: true }
      }
    ]
  },
  {
    path: '/system',
    component: Layout,
    redirect: '/system/status',
    meta: { title: '系统监控', icon: 'Monitor', requiresAdmin: true },
    children: [
      {
        path: 'status',
        name: 'SystemStatus',
        component: () => import('../views/system/status.vue'),
        meta: { title: '系统状态', requiresAdmin: true }
      },
      {
        path: 'model',
        name: 'ModelUsage',
        component: () => import('../views/system/model.vue'),
        meta: { title: '模型调用统计', requiresAdmin: true }
      },
      {
        path: 'filter',
        name: 'OutputFilterPolicy',
        component: () => import('../views/system/filter.vue'),
        meta: { title: '输出过滤策略', requiresAdmin: true }
      },
      {
        path: 'config',
        name: 'SystemConfig',
        component: () => import('../views/system/config.vue'),
        meta: { title: '系统配置', requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const userStore = useUserStore(pinia)
  const token = localStorage.getItem('token')

  if (to.path === '/login') {
    if (!token) {
      return true
    }

    if (!userStore.userInfo) {
      const info = await userStore.getUserInfo()
      if (!info) {
        return true
      }
    }

    return userStore.isAdmin ? '/dashboard' : true
  }

  if (to.path === '/403') {
    return true
  }

  if (to.path !== '/login' && !token) {
    return '/login'
  }

  if (token && !userStore.userInfo) {
    const info = await userStore.getUserInfo()
    if (!info) {
      return '/login'
    }
  }

  if (to.matched.some((record) => record.meta.requiresAdmin) && !userStore.isAdmin) {
    return '/403'
  }

  return true
})

export default router

