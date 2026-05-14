<template>
  <div class="page-shell">
    <section class="metric-grid">
      <article class="metric-card">
        <div class="metric-label">在线用户</div>
        <div class="metric-value">{{ systemStatus?.online_users ?? '--' }}</div>
        <div class="metric-extra">当前有效 token 数</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">已用内存</div>
        <div class="metric-value">{{ formatMemory(systemStatus?.memory_usage) }}</div>
        <div class="metric-extra">总内存 {{ formatMemory(systemStatus?.memory_total) }}</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">内存占用率</div>
        <div class="metric-value">{{ formatPercent(systemStatus?.memory_percent) }}</div>
        <a-progress :percent="systemStatus?.memory_percent || 0" :show-info="false" stroke-color="#d7a54a" />
      </article>
      <article class="metric-card">
        <div class="metric-label">运行时长</div>
        <div class="metric-value">{{ formatUptime(systemStatus?.uptime || 0) }}</div>
        <div class="metric-extra">服务自启动以来累计运行</div>
      </article>
    </section>

    <a-card :bordered="false" class="glass-card">
      <template #title>
        <p class="section-title">系统运行详情</p>
        <p class="section-desc">关键指标每 10 秒自动刷新，用于快速定位资源压力。</p>
      </template>

      <div class="detail-grid">
        <div class="detail-item">
          <span>运行时长</span>
          <strong>{{ formatUptime(systemStatus?.uptime || 0) }}</strong>
        </div>
        <div class="detail-item">
          <span>风险等级</span>
          <strong>{{ healthLevel }}</strong>
        </div>
        <div class="detail-item">
          <span>监控说明</span>
          <strong>基于 token、SQLite 与系统内存实时计算</strong>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { getSystemStatus } from '../../api/admin'

const systemStatus = ref<any>(null)
let timer: number | undefined

const loadSystemStatus = async () => {
  try {
    const response = await getSystemStatus()
    systemStatus.value = response.data
  } catch (error) {
    console.error('Load system status failed:', error)
  }
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${days} 天 ${hours} 小时 ${minutes} 分钟`
}

const formatPercent = (value?: number) => (value == null ? '--' : `${value.toFixed(1)}%`)
const formatMemory = (value?: number) => (value == null ? '--' : `${value.toFixed(2)} MB`)

const healthLevel = computed(() => {
  const maxValue = Math.max(systemStatus.value?.memory_percent || 0)

  if (maxValue >= 80) {
    return '高负载'
  }

  if (maxValue >= 60) {
    return '需关注'
  }

  return '稳定'
})

onMounted(() => {
  loadSystemStatus()
  timer = window.setInterval(loadSystemStatus, 10000)
})

onBeforeUnmount(() => {
  if (timer) {
    window.clearInterval(timer)
  }
})
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.detail-item {
  padding: 18px;
  border-radius: 20px;
  background: var(--surface-muted);
}

.detail-item span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.detail-item strong {
  font-size: 24px;
  color: var(--text-main);
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>

