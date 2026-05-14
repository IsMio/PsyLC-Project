<template>
  <div class="page-shell">
    <section class="metric-grid">
      <article class="metric-card">
        <div class="metric-label">在线用户</div>
        <div class="metric-value">{{ formatNumber(systemStatus?.online_users) }}</div>
        <div class="metric-extra">当前有效 token 数</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">已用内存</div>
        <div class="metric-value">{{ formatMemory(systemStatus?.memory_usage) }}</div>
        <div class="metric-extra">观察内存水位，避免高峰期抖动</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">内存占用率</div>
        <div class="metric-value">{{ formatPercent(systemStatus?.memory_percent) }}</div>
        <div class="metric-extra">关注内存峰值波动</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">总内存</div>
        <div class="metric-value">{{ formatMemory(systemStatus?.memory_total) }}</div>
        <div class="metric-extra">主机可用总内存</div>
      </article>
    </section>

    <a-row :gutter="[20, 20]">
      <a-col :xs="24" :xl="15">
        <a-card :bordered="false" class="glass-card">
          <template #title>
            <p class="section-title">模型调用概览</p>
            <p class="section-desc">按总量和当日数据快速判断模型成本与访问压力。</p>
          </template>

          <div class="summary-grid">
            <div class="summary-item">
              <span>总请求数</span>
              <strong>{{ formatNumber(modelUsage?.total_requests) }}</strong>
            </div>
            <div class="summary-item">
              <span>总 Token</span>
              <strong>{{ formatNumber(modelUsage?.total_tokens) }}</strong>
            </div>
            <div class="summary-item">
              <span>今日请求</span>
              <strong>{{ formatNumber(modelUsage?.today_requests) }}</strong>
            </div>
            <div class="summary-item">
              <span>今日 Token</span>
              <strong>{{ formatNumber(modelUsage?.today_tokens) }}</strong>
            </div>
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :xl="9">
        <a-card :bordered="false" class="glass-card uptime-card">
          <template #title>
            <p class="section-title">系统运行时长</p>
            <p class="section-desc">服务自上次启动以来的累计稳定运行时间。</p>
          </template>

          <div class="uptime-value">{{ formatUptime(systemStatus?.uptime || 0) }}</div>
          <div class="uptime-hint">数据每 30 秒自动刷新一次</div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { getModelUsage, getSystemStatus } from '../../api/admin'

const systemStatus = ref<any>(null)
const modelUsage = ref<any>(null)
let timer: number | undefined

const loadData = async () => {
  try {
    const [statusResponse, usageResponse] = await Promise.all([getSystemStatus(), getModelUsage()])
    systemStatus.value = statusResponse.data
    modelUsage.value = usageResponse.data
  } catch (error) {
    console.error('Load dashboard data failed:', error)
  }
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${days} 天 ${hours} 小时 ${minutes} 分钟`
}

const formatPercent = (value?: number) => (value == null ? '--' : `${value.toFixed(1)}%`)
const formatNumber = (value?: number) => (value == null ? '--' : value.toLocaleString('zh-CN'))
const formatMemory = (value?: number) => (value == null ? '--' : `${value.toFixed(2)} MB`)

onMounted(() => {
  loadData()
  timer = window.setInterval(loadData, 30000)
})

onBeforeUnmount(() => {
  if (timer) {
    window.clearInterval(timer)
  }
})
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.summary-item {
  padding: 18px;
  border-radius: 20px;
  background: var(--surface-muted);
}

.summary-item span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.summary-item strong {
  font-size: 28px;
  color: var(--text-main);
}

.uptime-card {
  min-height: 100%;
}

.uptime-value {
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  line-height: 1.2;
  color: var(--text-main);
}

.uptime-hint {
  margin-top: 14px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>

