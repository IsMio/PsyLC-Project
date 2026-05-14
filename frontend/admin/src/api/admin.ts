import request from './request'

export interface KnowledgePayload {
  topic: string
  title: string
  type: string
  content: string
}

export interface OutputFilterRule {
  reason: string
  pattern: string
  enabled: boolean
}

export interface OutputFilterPolicy {
  enabled: boolean | number
  review_enabled: boolean | number
  rules: OutputFilterRule[]
  templates: Record<string, string>
  updated_by?: string | null
  updated_at?: number | null
}

export const createKnowledgeText = (data: KnowledgePayload) => {
  return request({
    url: '/admin/knowledge-base/text',
    method: 'post',
    data
  })
}

export const uploadKnowledgeFile = (data: FormData) => {
  return request({
    url: '/admin/knowledge-base/file',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const importKnowledgeDataset = (data: FormData) => {
  return request({
    url: '/admin/knowledge-base/dataset',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getKnowledgeBaseList = (params: {
  pageNum?: number
  pageSize?: number
  keyword?: string
  status?: string
}) => {
  return request({
    url: '/admin/knowledge-base/list',
    method: 'get',
    params
  })
}

export const getKnowledgeBaseDetail = (id: string) => {
  return request({
    url: `/admin/knowledge-base/${id}`,
    method: 'get'
  })
}

export const updateKnowledgeBase = (id: string, data: KnowledgePayload) => {
  return request({
    url: `/admin/knowledge-base/${id}`,
    method: 'put',
    data
  })
}

export const deleteKnowledgeBase = (id: string) => {
  return request({
    url: `/admin/knowledge-base/${id}`,
    method: 'delete'
  })
}

export const getKnowledgeJobs = (params: {
  pageNum?: number
  pageSize?: number
  documentId?: string
  batchId?: string
}) => {
  return request({
    url: '/admin/knowledge-base/jobs',
    method: 'get',
    params
  })
}

export const getKnowledgeBatches = (params: {
  pageNum?: number
  pageSize?: number
}) => {
  return request({
    url: '/admin/knowledge-base/batches',
    method: 'get',
    params
  })
}

export const getKnowledgeBatchDetail = (batchId: string) => {
  return request({
    url: `/admin/knowledge-base/batches/${batchId}`,
    method: 'get'
  })
}

export const getKnowledgeJobDetail = (jobId: string) => {
  return request({
    url: `/admin/knowledge-base/jobs/${jobId}`,
    method: 'get'
  })
}

export const retryKnowledgeJob = (jobId: string) => {
  return request({
    url: `/admin/knowledge-base/jobs/${jobId}/retry`,
    method: 'post'
  })
}

export const getUserList = (params: {
  pageNum?: number
  pageSize?: number
  keyword?: string
}) => {
  return request({
    url: '/admin/user/list',
    method: 'get',
    params
  })
}

export const updateUser = (data: {
  userId: string
  display_name: string
  roles: string[]
  avatar: string
}) => {
  return request({
    url: '/admin/user',
    method: 'put',
    data
  })
}

export const deleteUser = (ids: string) => {
  return request({
    url: `/admin/user/${ids}`,
    method: 'delete'
  })
}

export const getSystemStatus = () => {
  return request({
    url: '/admin/system/status',
    method: 'get'
  })
}

export const getModelUsage = () => {
  return request({
    url: '/admin/model/usage',
    method: 'get'
  })
}

export const getModelUsageDetail = (params: {
  days?: number
}) => {
  return request({
    url: '/admin/model/usage/detail',
    method: 'get',
    params
  })
}

export const healthCheck = () => {
  return request({
    url: '/admin/health',
    method: 'get'
  })
}

export const getSystemConfig = () => {
  return request({
    url: '/admin/system/config',
    method: 'get'
  })
}

export const updateSystemConfig = (config: Record<string, any>) => {
  return request({
    url: '/admin/system/config',
    method: 'put',
    data: { config }
  })
}

export const restartSystem = () => {
  return request({
    url: '/admin/system/restart',
    method: 'post'
  })
}

export const previewMineruChunks = (data: FormData) => {
  return request({
    url: '/admin/system/mineru/preview',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getOutputFilterPolicy = () => {
  return request({
    url: '/admin/output-filter/policy',
    method: 'get'
  })
}

export const updateOutputFilterPolicy = (data: OutputFilterPolicy) => {
  return request({
    url: '/admin/output-filter/policy',
    method: 'put',
    data
  })
}
