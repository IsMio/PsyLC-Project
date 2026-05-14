<template>
  <div class="page-shell">
    <a-card :bordered="false" class="glass-card">
      <div class="page-toolbar">
        <div>
          <p class="section-title">知识库管理</p>
          <p class="section-desc">维护文档元数据、导入多轮数据集，并查看异步入库批次进度。</p>
        </div>
        <div class="page-toolbar-right">
          <a-input
            v-model:value="searchKeyword"
            allow-clear
            size="large"
            class="search-input"
            placeholder="搜索标题、主题或内容"
            @pressEnter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
          <a-select v-model:value="statusFilter" allow-clear size="large" style="width: 150px">
            <a-select-option value="pending">待处理</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="success">成功</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>
          <a-button size="large" @click="handleReset">重置</a-button>
          <a-button type="primary" size="large" @click="handleSearch">搜索</a-button>
          <a-button type="primary" ghost size="large" @click="router.push('/knowledge/create')">新建知识</a-button>
          <a-button type="primary" size="large" @click="openDatasetDrawer">导入数据集</a-button>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="knowledgeList"
        :pagination="pagination"
        row-key="id"
        class="data-table"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="knowledge-title-cell">
              <strong>{{ record.title }}</strong>
              <span>{{ record.topic }} / {{ record.doc_type }}</span>
            </div>
          </template>

          <template v-else-if="column.key === 'source_type'">
            {{ sourceTypeLabel(record.source_type) }}
          </template>

          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColorMap[record.status] || 'default'">{{ statusLabelMap[record.status] || record.status }}</a-tag>
          </template>

          <template v-else-if="column.key === 'chunk_count'">
            {{ record.chunk_count ?? 0 }}
          </template>

          <template v-else-if="column.key === 'updated_at'">
            {{ formatDate(record.updated_at || record.created_at) }}
          </template>

          <template v-else-if="column.key === 'error_message'">
            <span class="error-text">{{ record.error_message || '--' }}</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" @click="handleEdit(record.id)">编辑</a-button>
              <a-button type="link" @click="handleViewJob(record.id)">任务详情</a-button>
              <a-button v-if="record.status === 'failed'" type="link" @click="handleRetry(record.id)">重试</a-button>
              <a-popconfirm title="确认删除这条知识吗？" ok-text="删除" cancel-text="取消" @confirm="handleDelete(record.id)">
                <a-button type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-drawer
      :open="datasetDrawerVisible"
      title="导入数据集"
      width="760"
      @close="closeDatasetDrawer"
    >
      <div class="dataset-panel">
        <a-alert
          type="info"
          show-icon
          message="有效对话记录数量不限，系统会异步导入，并按每秒 3 条任务的节奏逐步入队。"
        />

        <a-tabs v-model:activeKey="datasetImportMode" class="dataset-tabs">
          <a-tab-pane key="upload" tab="上传 JSON 文件">
            <a-upload-dragger
              :before-upload="beforeDatasetUpload"
              :show-upload-list="true"
              accept=".json"
              :max-count="1"
            >
              <p class="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p class="ant-upload-text">点击或拖拽 JSON 数据集文件到此处</p>
              <p class="ant-upload-hint">每条完整多轮对话会变成一篇知识文档，任务会按每秒 3 条的速度异步进入入库队列。</p>
            </a-upload-dragger>

            <div class="dataset-actions">
              <a-space>
                <a-button :disabled="!datasetFile" @click="clearSelectedFile">清空文件</a-button>
                <a-button type="primary" :loading="datasetSubmitting" @click="submitDatasetUpload">开始导入</a-button>
              </a-space>
            </div>
          </a-tab-pane>

          <a-tab-pane key="path" tab="服务器本地路径">
            <a-form layout="vertical">
              <a-form-item label="数据集路径">
                <a-input
                  v-model:value="datasetPath"
                  size="large"
                  placeholder="例如：C:\\Users\\Mio\\Downloads\\PsyDTCorpus_train_mulit_turn_packing.json"
                />
              </a-form-item>
            </a-form>

            <div class="dataset-actions">
              <a-button type="primary" :loading="datasetSubmitting" @click="submitDatasetPath">开始导入</a-button>
            </div>
          </a-tab-pane>
        </a-tabs>

        <div class="dataset-progress-header">
          <div>
            <div class="section-subtitle">最近导入批次</div>
            <div class="section-caption">按批次查看真实进度，失败样本也会计入已处理数量。</div>
          </div>
          <a-space>
            <a-switch v-model:checked="autoRefreshBatches" checked-children="自动刷新" un-checked-children="已暂停" />
            <a-button @click="refreshBatchPanel">立即刷新</a-button>
          </a-space>
        </div>

        <a-list bordered :data-source="recentBatches" class="batch-list">
          <template #renderItem="{ item }">
            <a-list-item>
              <div class="batch-item" :class="{ selected: selectedBatchId === item.id }" @click="selectBatch(item.id)">
                <div class="batch-item-top">
                  <div>
                    <div class="batch-title">{{ item.source_name }}</div>
                    <div class="batch-meta">批次ID: {{ item.id }}</div>
                  </div>
                  <a-tag :color="batchStatusColor(item.status)">{{ batchStatusLabel(item.status) }}</a-tag>
                </div>
                <div class="batch-progress-row">
                  <span>{{ item.completed_count }}/{{ item.total_count }} 已完成</span>
                  <span>成功 {{ item.success_count }} / 失败 {{ item.failed_count }}</span>
                </div>
                <a-progress :percent="batchPercent(item)" :status="progressStatus(item)" />
                <div class="batch-meta-row">
                  <span>创建时间: {{ formatDate(item.created_at) }}</span>
                  <span>更新时间: {{ formatDate(item.updated_at) }}</span>
                </div>
              </div>
            </a-list-item>
          </template>
          <template #locale>
            <div class="empty-jobs">暂无导入批次</div>
          </template>
        </a-list>

        <div class="dataset-progress-header sub-panel-header">
          <div>
            <div class="section-subtitle">批次任务明细</div>
            <div class="section-caption">展示当前选中批次下的异步入库任务。</div>
          </div>
        </div>

        <a-list bordered :data-source="selectedBatchJobs" class="job-list">
          <template #renderItem="{ item }">
            <a-list-item>
              <div class="job-item">
                <div class="job-item-top">
                  <div>
                    <div class="job-title">{{ item.documentTitle || item.document_id }}</div>
                    <div class="job-meta">任务ID: {{ item.id }}</div>
                  </div>
                  <a-tag :color="statusColorMap[item.status] || 'default'">{{ statusLabelMap[item.status] || item.status }}</a-tag>
                </div>
                <div class="job-meta-row">
                  <span>类型: {{ item.job_type }}</span>
                  <span>创建时间: {{ formatDate(item.created_at) }}</span>
                  <span v-if="item.finished_at">完成时间: {{ formatDate(item.finished_at) }}</span>
                </div>
                <div v-if="item.error_message" class="job-error">{{ item.error_message }}</div>
                <div class="job-actions">
                  <a-button type="link" @click.stop="handleOpenJobDetail(item.id)">查看详情</a-button>
                </div>
              </div>
            </a-list-item>
          </template>
          <template #locale>
            <div class="empty-jobs">请选择一个批次查看任务</div>
          </template>
        </a-list>
      </div>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { InboxOutlined, SearchOutlined } from '@ant-design/icons-vue'
import {
  deleteKnowledgeBase,
  getKnowledgeBaseList,
  getKnowledgeBatchDetail,
  getKnowledgeBatches,
  getKnowledgeJobs,
  importKnowledgeDataset,
  retryKnowledgeJob
} from '../../api/admin'

interface KnowledgeItem {
  id: string
  topic: string
  title: string
  doc_type: string
  source_type: string
  status: string
  chunk_count: number
  error_message?: string
  created_at: number
  updated_at: number
}

interface JobItem {
  id: string
  document_id: string
  job_type: string
  status: string
  created_at: number
  finished_at?: number
  error_message?: string
  documentTitle?: string
}

interface BatchItem {
  id: string
  source_name: string
  total_count: number
  completed_count: number
  success_count: number
  failed_count: number
  status: string
  created_at: number
  updated_at: number
}

const router = useRouter()
const searchKeyword = ref('')
const statusFilter = ref<string | undefined>()
const knowledgeList = ref<KnowledgeItem[]>([])
const datasetDrawerVisible = ref(false)
const datasetImportMode = ref<'upload' | 'path'>('upload')
const datasetFile = ref<File | null>(null)
const datasetPath = ref('')
const datasetSubmitting = ref(false)
const recentBatches = ref<BatchItem[]>([])
const selectedBatchId = ref('')
const selectedBatchJobs = ref<JobItem[]>([])
const autoRefreshBatches = ref(true)
let batchesTimer: number | null = null

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const statusLabelMap: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  success: '成功',
  failed: '失败'
}

const statusColorMap: Record<string, string> = {
  pending: 'gold',
  processing: 'processing',
  success: 'success',
  failed: 'error'
}

const columns = [
  { title: '标题 / 分类', key: 'title' },
  { title: '来源', key: 'source_type', width: 120 },
  { title: '状态', key: 'status', width: 110 },
  { title: '分块数', key: 'chunk_count', width: 90 },
  { title: '错误信息', key: 'error_message' },
  { title: '更新时间', key: 'updated_at', width: 180 },
  { title: '操作', key: 'action', width: 180 }
]

const formatDate = (timestamp?: number) => (timestamp ? new Date(timestamp * 1000).toLocaleString('zh-CN') : '--')

const sourceTypeLabel = (sourceType: string) => {
  if (sourceType === 'file') return '文件导入'
  if (sourceType === 'text') return '文本导入'
  return sourceType || '--'
}

const batchStatusLabel = (status: string) => {
  if (status === 'finished') return '已完成'
  if (status === 'processing') return '处理中'
  return status || '--'
}

const batchStatusColor = (status: string) => {
  if (status === 'finished') return 'success'
  if (status === 'processing') return 'processing'
  return 'default'
}

const batchPercent = (item: BatchItem) => {
  if (!item.total_count) return 0
  return Math.min(100, Math.round((item.completed_count / item.total_count) * 100))
}

const progressStatus = (item: BatchItem) => {
  if (item.failed_count > 0) return 'exception'
  if (item.completed_count >= item.total_count) return 'success'
  return 'active'
}

const loadKnowledgeList = async () => {
  const response = await getKnowledgeBaseList({
    pageNum: pagination.current,
    pageSize: pagination.pageSize,
    keyword: searchKeyword.value,
    status: statusFilter.value
  })

  knowledgeList.value = response.data.rows || []
  pagination.total = response.data.total || 0
}

const buildDocumentTitleMap = () => {
  const titleMap = new Map<string, string>()
  for (const item of knowledgeList.value) {
    titleMap.set(item.id, item.title)
  }
  return titleMap
}

const loadSelectedBatchJobs = async (batchId: string) => {
  if (!batchId) {
    selectedBatchJobs.value = []
    return
  }
  const response = await getKnowledgeBatchDetail(batchId)
  const titleMap = buildDocumentTitleMap()
  selectedBatchJobs.value = (response.data.jobs || []).map((job: JobItem) => ({
    ...job,
    documentTitle: titleMap.get(job.document_id) || ''
  }))
}

const loadRecentBatches = async () => {
  const response = await getKnowledgeBatches({ pageNum: 1, pageSize: 10 })
  recentBatches.value = response.data.rows || []
  if (!selectedBatchId.value && recentBatches.value.length > 0) {
    selectedBatchId.value = recentBatches.value[0].id
  }
  if (selectedBatchId.value) {
    const exists = recentBatches.value.some((item) => item.id === selectedBatchId.value)
    if (!exists) {
      selectedBatchId.value = recentBatches.value[0]?.id || ''
    }
  }
  await loadSelectedBatchJobs(selectedBatchId.value)
}

const refreshBatchPanel = async () => {
  await Promise.all([loadKnowledgeList(), loadRecentBatches()])
}

const selectBatch = async (batchId: string) => {
  selectedBatchId.value = batchId
  await loadSelectedBatchJobs(batchId)
}

const startBatchPolling = () => {
  stopBatchPolling()
  batchesTimer = window.setInterval(() => {
    if (datasetDrawerVisible.value && autoRefreshBatches.value) {
      loadRecentBatches()
    }
  }, 3000)
}

const stopBatchPolling = () => {
  if (batchesTimer !== null) {
    window.clearInterval(batchesTimer)
    batchesTimer = null
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadKnowledgeList()
}

const handleReset = () => {
  searchKeyword.value = ''
  statusFilter.value = undefined
  handleSearch()
}

const handleTableChange = (page: { current?: number; pageSize?: number }) => {
  pagination.current = page.current || 1
  pagination.pageSize = page.pageSize || 10
  loadKnowledgeList()
}

const handleEdit = (id: string) => {
  router.push(`/knowledge/edit/${id}`)
}

const handleViewJob = async (documentId: string) => {
  const jobs = await getKnowledgeJobs({ documentId, pageSize: 1 })
  const job = jobs.data.rows?.[0]
  if (!job) {
    message.error('未找到任务详情')
    return
  }
  router.push(`/knowledge/jobs/${job.id}`)
}

const handleOpenJobDetail = (jobId: string) => {
  router.push(`/knowledge/jobs/${jobId}`)
}

const handleRetry = async (documentId: string) => {
  const jobs = await getKnowledgeJobs({ documentId, pageSize: 1 })
  const job = jobs.data.rows?.[0]
  if (!job) {
    message.error('未找到可重试任务')
    return
  }
  await retryKnowledgeJob(job.id)
  message.success('任务已重新入队')
  await refreshBatchPanel()
}

const handleDelete = async (id: string) => {
  await deleteKnowledgeBase(id)
  message.success('知识条目已删除')
  await refreshBatchPanel()
}

const beforeDatasetUpload = (file: File) => {
  datasetFile.value = file
  return false
}

const clearSelectedFile = () => {
  datasetFile.value = null
}

const handleImportSuccess = async (response: any) => {
  const batchId = response.data.batch?.id || ''
  const total = response.data.batch?.total_count || response.data.total || 0
  message.success(`导入请求已提交，本次批次共 ${total} 条有效记录，将按每秒 3 条异步入队`)
  if (batchId) {
    selectedBatchId.value = batchId
  }
  await refreshBatchPanel()
  datasetFile.value = null
}

const submitDatasetUpload = async () => {
  if (!datasetFile.value) {
    message.error('请选择 JSON 数据集文件')
    return
  }
  datasetSubmitting.value = true
  try {
    const data = new FormData()
    data.append('file', datasetFile.value)
    const response = await importKnowledgeDataset(data)
    await handleImportSuccess(response)
  } finally {
    datasetSubmitting.value = false
  }
}

const submitDatasetPath = async () => {
  const value = datasetPath.value.trim()
  if (!value) {
    message.error('请输入服务器可访问的数据集路径')
    return
  }
  datasetSubmitting.value = true
  try {
    const data = new FormData()
    data.append('file_path', value)
    const response = await importKnowledgeDataset(data)
    await handleImportSuccess(response)
  } finally {
    datasetSubmitting.value = false
  }
}

const openDatasetDrawer = async () => {
  datasetDrawerVisible.value = true
  await refreshBatchPanel()
}

const closeDatasetDrawer = () => {
  datasetDrawerVisible.value = false
}

watch(
  () => datasetDrawerVisible.value,
  (visible) => {
    if (visible) {
      startBatchPolling()
    } else {
      stopBatchPolling()
    }
  }
)

onMounted(async () => {
  await loadKnowledgeList()
})

onBeforeUnmount(() => {
  stopBatchPolling()
})
</script>

<style scoped>
.search-input {
  width: min(320px, 100%);
}

.data-table {
  margin-top: 20px;
}

.knowledge-title-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.knowledge-title-cell span,
.error-text,
.section-caption,
.job-meta,
.job-meta-row,
.batch-meta,
.batch-meta-row,
.batch-progress-row {
  color: var(--text-secondary);
}

.dataset-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dataset-tabs {
  margin-top: 8px;
}

.dataset-actions {
  margin-top: 16px;
}

.dataset-progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
}

.sub-panel-header {
  margin-top: 4px;
}

.section-subtitle {
  font-size: 16px;
  font-weight: 700;
}

.batch-list,
.job-list {
  max-height: 420px;
  overflow: auto;
}

.batch-item,
.job-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.batch-item {
  cursor: pointer;
  padding: 4px 0;
}

.batch-item.selected {
  background: rgba(24, 144, 255, 0.06);
}

.batch-item-top,
.job-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.batch-title,
.job-title {
  font-weight: 700;
}

.batch-progress-row,
.batch-meta-row,
.job-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.job-error {
  color: #cf1322;
  white-space: pre-wrap;
  word-break: break-word;
}

.job-actions {
  display: flex;
  justify-content: flex-end;
}

.empty-jobs {
  padding: 24px 0;
  text-align: center;
  color: var(--text-secondary);
}

@media (max-width: 960px) {
  .dataset-progress-header,
  .batch-item-top,
  .job-item-top {
    flex-direction: column;
    align-items: stretch;
  }

  .job-actions {
    justify-content: flex-start;
  }
}
</style>
