<template>
  <div class="page-shell">
    <a-card :bordered="false" class="glass-card">
      <template #title>
        <p class="section-title">入库任务详情</p>
        <p class="section-desc">查看任务状态、文档信息，以及每个 chunk 的预览内容。</p>
      </template>

      <a-skeleton active :loading="loading">
        <a-descriptions bordered :column="2" size="small">
          <a-descriptions-item label="任务 ID">{{ detail.job?.id }}</a-descriptions-item>
          <a-descriptions-item label="任务状态">{{ detail.job?.status }}</a-descriptions-item>
          <a-descriptions-item label="任务类型">{{ detail.job?.job_type }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDate(detail.job?.created_at) }}</a-descriptions-item>
          <a-descriptions-item label="文档标题">{{ detail.document?.title }}</a-descriptions-item>
          <a-descriptions-item label="主题 / 类型">{{ detail.document?.topic }} / {{ detail.document?.doc_type }}</a-descriptions-item>
          <a-descriptions-item label="分块数">{{ detail.document?.chunk_count ?? detail.chunks.length }}</a-descriptions-item>
          <a-descriptions-item label="错误信息">{{ detail.document?.error_message || '--' }}</a-descriptions-item>
        </a-descriptions>

        <div class="chunk-section">
          <div class="section-subtitle">Chunk 预览</div>
          <a-list bordered :data-source="detail.chunks">
            <template #renderItem="{ item }">
              <a-list-item>
                <div class="chunk-item">
                  <div class="chunk-title">Chunk {{ item.chunk_index }}</div>
                  <div class="chunk-content">{{ item.content }}</div>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </div>

        <a-space class="page-actions">
          <a-button @click="router.push('/knowledge/list')">返回列表</a-button>
        </a-space>
      </a-skeleton>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getKnowledgeJobDetail } from '../../api/admin'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const detail = reactive<any>({
  job: null,
  document: null,
  chunks: []
})

const loadDetail = async () => {
  loading.value = true
  try {
    const response = await getKnowledgeJobDetail(route.params.id as string)
    detail.job = response.data.job
    detail.document = response.data.document
    detail.chunks = response.data.chunks || []
  } finally {
    loading.value = false
  }
}

const formatDate = (timestamp?: number) => (timestamp ? new Date(timestamp * 1000).toLocaleString('zh-CN') : '--')

onMounted(loadDetail)
</script>

<style scoped>
.chunk-section {
  margin-top: 24px;
}

.section-subtitle {
  margin-bottom: 12px;
  font-weight: 700;
}

.chunk-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chunk-title {
  font-weight: 700;
}

.chunk-content {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-secondary);
}

.page-actions {
  margin-top: 20px;
}
</style>
