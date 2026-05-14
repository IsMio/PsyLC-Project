<template>
  <div class="page-shell">
    <section class="metric-grid">
      <article class="metric-card">
        <div class="metric-label">总请求数</div>
        <div class="metric-value">{{ formatNumber(modelUsage?.total_requests) }}</div>
        <div class="metric-extra">累计请求次数</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">总 Token</div>
        <div class="metric-value">{{ formatNumber(modelUsage?.total_tokens) }}</div>
        <div class="metric-extra">累计 token 消耗</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">今日请求</div>
        <div class="metric-value">{{ formatNumber(modelUsage?.today_requests) }}</div>
        <div class="metric-extra">过去 24 小时访问量</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">今日 Token</div>
        <div class="metric-value">{{ formatNumber(modelUsage?.today_tokens) }}</div>
        <div class="metric-extra">过去 24 小时 token 消耗</div>
      </article>
    </section>

    <a-card :bordered="false" class="glass-card">
      <div class="page-toolbar trend-toolbar">
        <div>
          <p class="section-title">模型调用趋势</p>
          <p class="section-desc">按天查看请求量和 Token 消耗，便于发现异常峰值。</p>
        </div>
        <a-select v-model:value="days" style="width: 140px" size="large" @change="loadModelUsageDetail">
          <a-select-option :value="7">最近 7 天</a-select-option>
          <a-select-option :value="30">最近 30 天</a-select-option>
          <a-select-option :value="90">最近 90 天</a-select-option>
        </a-select>
      </div>

      <div v-if="modelUsageDetail.length === 0" class="empty-state">暂无趋势数据</div>

      <div v-else class="trend-list">
        <div v-for="item in modelUsageDetail" :key="item.date" class="trend-row">
          <div class="trend-date">{{ item.date }}</div>
          <div class="trend-bars">
            <div class="trend-bar-group">
              <div class="trend-bar-meta">
                <span>请求数</span>
                <strong>{{ item.requests }}</strong>
              </div>
              <div class="trend-track">
                <div class="trend-fill" :style="{ width: getBarWidth(item.requests, 'requests') }"></div>
              </div>
            </div>
            <div class="trend-bar-group">
              <div class="trend-bar-meta">
                <span>Token</span>
                <strong>{{ item.tokens }}</strong>
              </div>
              <div class="trend-track token-track">
                <div class="trend-fill token-fill" :style="{ width: getBarWidth(item.tokens, 'tokens') }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getModelUsage, getModelUsageDetail } from '../../api/admin'

interface UsageDetailItem {
  date: string
  requests: number
  tokens: number
}

const modelUsage = ref<any>(null)
const modelUsageDetail = ref<UsageDetailItem[]>([])
const days = ref(7)

const maxRequests = computed(() => Math.max(...modelUsageDetail.value.map((item) => item.requests), 1))
const maxTokens = computed(() => Math.max(...modelUsageDetail.value.map((item) => item.tokens), 1))

const loadModelUsage = async () => {
  try {
    const response = await getModelUsage()
    modelUsage.value = response.data
  } catch (error) {
    console.error('Load model usage failed:', error)
  }
}

const loadModelUsageDetail = async () => {
  try {
    const response = await getModelUsageDetail({ days: days.value })
    modelUsageDetail.value = (response.data || []).map((item: any) => ({
      date: item.date,
      requests: item.requests ?? item.calls ?? 0,
      tokens: item.tokens ?? 0
    }))
  } catch (error) {
    console.error('Load model usage detail failed:', error)
  }
}

const getBarWidth = (value: number, type: 'requests' | 'tokens') => {
  const max = type === 'requests' ? maxRequests.value : maxTokens.value
  return `${Math.max((value / max) * 100, 4)}%`
}

const formatNumber = (value?: number) => (value == null ? '--' : value.toLocaleString('zh-CN'))

onMounted(() => {
  loadModelUsage()
  loadModelUsageDetail()
})
</script>

<style scoped>
.trend-toolbar {
  margin-bottom: 12px;
}

.empty-state {
  padding: 64px 0;
  text-align: center;
  color: var(--text-secondary);
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.trend-row {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 20px;
  align-items: center;
}

.trend-date {
  font-weight: 600;
  color: var(--brand-strong);
}

.trend-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-bar-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trend-bar-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-secondary);
}

.trend-track {
  height: 12px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(23, 50, 92, 0.08);
}

.token-track {
  background: rgba(215, 165, 74, 0.14);
}

.trend-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #17325c 0%, #426aa6 100%);
}

.token-fill {
  background: linear-gradient(90deg, #d7a54a 0%, #f0c979 100%);
}

@media (max-width: 768px) {
  .trend-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
</style>

