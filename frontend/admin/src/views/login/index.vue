<template>
  <div class="login-page">
    <div class="login-panel">
      <div class="login-hero">
        <span class="status-pill">PsyLC 管理后台</span>
        <h1>集中处理用户、知识库与系统状态</h1>
        <p>使用具备管理员角色的账户登录后即可进入控制台。</p>
      </div>

      <a-card :bordered="false" class="login-card">
        <template #title>
          <div class="login-card-title">管理员登录</div>
        </template>

        <a-form ref="formRef" :model="formState" :rules="rules" layout="vertical">
          <a-form-item label="用户名" name="username">
            <a-input v-model:value="formState.username" size="large" placeholder="请输入用户名" />
          </a-form-item>

          <a-form-item label="密码" name="password">
            <a-input-password
              v-model:value="formState.password"
              size="large"
              placeholder="请输入密码"
              @pressEnter="handleLogin"
            />
          </a-form-item>

          <a-button type="primary" block size="large" :loading="loading" @click="handleLogin">
            登录
          </a-button>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { message } from 'ant-design-vue'
import { useUserStore } from '../../store/modules/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const formState = reactive({
  username: '',
  password: ''
})

const rules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) {
    return
  }

  try {
    await formRef.value.validate()
    loading.value = true
    const success = await userStore.loginAction(formState.username, formState.password)

    if (!success) {
      message.error('用户名或密码错误')
      return
    }

      message.success('登录成功')
      if (!userStore.isAdmin) {
        message.error('当前账号没有管理员权限')
        await userStore.logoutAction()
        return
      }

      router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background:
    radial-gradient(circle at top left, rgba(247, 215, 148, 0.24), transparent 28%),
    radial-gradient(circle at right bottom, rgba(23, 50, 92, 0.24), transparent 34%),
    var(--body-bg);
}

.login-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 440px);
  gap: 28px;
  width: min(1080px, 100%);
  align-items: center;
}

.login-hero {
  color: var(--brand-strong);
}

.login-hero h1 {
  margin: 18px 0 14px;
  font-size: clamp(34px, 5vw, 54px);
  line-height: 1.08;
}

.login-hero p {
  max-width: 520px;
  font-size: 16px;
  color: var(--text-secondary);
}

.login-card {
  border-radius: 28px;
  background: color-mix(in srgb, var(--surface-solid) 92%, transparent);
  box-shadow: 0 24px 60px rgba(9, 23, 44, 0.22);
}

.login-card-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

@media (max-width: 900px) {
  .login-panel {
    grid-template-columns: 1fr;
  }

  .login-hero {
    text-align: center;
  }

  .login-hero p {
    margin-inline: auto;
  }
}
</style>

