<template>
  <div class="page-shell form-shell">
    <a-card :bordered="false" class="glass-card">
      <template #title>
        <p class="section-title">新建知识库</p>
        <p class="section-desc">支持直接录入文本，或上传 PDF / 文本文档后异步写入 Chroma。</p>
      </template>

      <a-radio-group v-model:value="mode" button-style="solid" class="mode-switch">
        <a-radio-button value="text">直接录入</a-radio-button>
        <a-radio-button value="file">文件导入</a-radio-button>
      </a-radio-group>

      <a-form ref="formRef" :model="formState" :rules="rules" layout="vertical">
        <a-form-item label="主题" name="topic">
          <a-input v-model:value="formState.topic" size="large" placeholder="如：抑郁、焦虑、睡眠" />
        </a-form-item>

        <a-form-item label="标题" name="title">
          <a-input v-model:value="formState.title" size="large" placeholder="请输入知识标题" />
        </a-form-item>

        <a-form-item label="类型" name="type">
          <a-input v-model:value="formState.type" size="large" placeholder="如：pdf、article、note" />
        </a-form-item>

        <a-form-item v-if="mode === 'text'" label="内容" name="content">
          <a-textarea v-model:value="formState.content" :rows="10" placeholder="请输入知识内容" />
        </a-form-item>

        <a-form-item v-else label="文件" name="file">
          <input type="file" accept=".txt,.md,.pdf,.docx,.html,.htm" @change="handleFileChange" />
          <div class="upload-hint">支持 txt、md、pdf、docx、html，提交后后台将异步切块并入库。</div>
          <a-space class="preview-actions">
            <a-button :disabled="!selectedFile" @click="handlePreviewChunks">预览分割</a-button>
          </a-space>
          <a-alert
            v-if="previewResult"
            class="preview-alert"
            type="info"
            show-icon
            :message="`共 ${previewResult.count} 段，${previewResult.used_structured_blocks ? '已使用 MinerU 结构化段落' : '未命中结构化段落，使用回退结果'}`"
          />
          <a-list
            v-if="previewResult"
            bordered
            class="preview-list"
            :data-source="previewResult.chunks"
            size="small"
          >
            <template #renderItem="{ item, index }">
              <a-list-item>
                <div class="chunk-item">
                  <div class="chunk-title">Chunk {{ index + 1 }}</div>
                  <div class="chunk-content">{{ item }}</div>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-form-item>

        <a-space>
          <a-button type="primary" size="large" @click="handleSubmit">提交</a-button>
          <a-button size="large" @click="router.push('/knowledge/list')">取消</a-button>
        </a-space>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { createKnowledgeText, previewMineruChunks, uploadKnowledgeFile } from '../../api/admin'

const router = useRouter()
const formRef = ref<FormInstance>()
const mode = ref<'text' | 'file'>('text')
const selectedFile = ref<File | null>(null)
const previewResult = ref<{ chunks: string[]; count: number; used_structured_blocks: boolean } | null>(null)
const formState = reactive({
  topic: '',
  title: '',
  type: '',
  content: ''
})

const rules: Record<string, Rule[]> = {
  topic: [{ required: true, message: '请输入主题', trigger: 'blur' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  type: [{ required: true, message: '请输入类型', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

const handleFileChange = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0] || null
  selectedFile.value = file
  previewResult.value = null
}

const handlePreviewChunks = async () => {
  if (!selectedFile.value) {
    message.error('请选择上传文件')
    return
  }
  const data = new FormData()
  data.append('file', selectedFile.value)
  const response = await previewMineruChunks(data)
  previewResult.value = response.data
}

const handleSubmit = async () => {
  if (!formRef.value) {
    return
  }

  await formRef.value.validate(['topic', 'title', 'type', ...(mode.value === 'text' ? ['content'] : [])])

  if (mode.value === 'text') {
    await createKnowledgeText({ ...formState })
  } else {
    if (!selectedFile.value) {
      message.error('请选择上传文件')
      return
    }
    const data = new FormData()
    data.append('topic', formState.topic)
    data.append('title', formState.title)
    data.append('type', formState.type)
    data.append('file', selectedFile.value)
    await uploadKnowledgeFile(data)
  }

  message.success('知识文档已提交，后台将异步处理')
  router.push('/knowledge/list')
}
</script>

<style scoped>
.mode-switch {
  margin-bottom: 20px;
}

.upload-hint {
  margin-top: 8px;
  color: var(--text-secondary);
}

.preview-actions {
  margin-top: 12px;
}

.preview-alert {
  margin-top: 12px;
}

.preview-list {
  margin-top: 12px;
}

.chunk-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chunk-title {
  font-weight: 700;
}

.chunk-content {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-secondary);
}
</style>
