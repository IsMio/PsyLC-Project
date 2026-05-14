<template>
  <div class="page-shell form-shell">
    <a-card :bordered="false" class="glass-card">
      <template #title>
        <p class="section-title">编辑知识库</p>
        <p class="section-desc">修改基础元数据与内容后，将重新进入异步入库队列。</p>
      </template>

      <a-skeleton active :loading="loading">
        <a-form ref="formRef" :model="formState" :rules="rules" layout="vertical">
          <a-form-item label="主题" name="topic">
            <a-input v-model:value="formState.topic" size="large" placeholder="请输入主题" />
          </a-form-item>

          <a-form-item label="标题" name="title">
            <a-input v-model:value="formState.title" size="large" placeholder="请输入知识标题" />
          </a-form-item>

          <a-form-item label="类型" name="type">
            <a-input v-model:value="formState.type" size="large" placeholder="请输入知识类型" />
          </a-form-item>

          <a-form-item label="内容" name="content">
            <a-textarea v-model:value="formState.content" :rows="10" placeholder="请输入知识内容" />
          </a-form-item>

          <a-space>
            <a-button type="primary" size="large" @click="handleSubmit">保存</a-button>
            <a-button size="large" @click="router.push('/knowledge/list')">取消</a-button>
          </a-space>
        </a-form>
      </a-skeleton>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { getKnowledgeBaseDetail, updateKnowledgeBase } from '../../api/admin'

const router = useRouter()
const route = useRoute()
const id = route.params.id as string
const loading = ref(true)
const formRef = ref<FormInstance>()
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

const loadKnowledgeDetail = async () => {
  loading.value = true
  try {
    const response = await getKnowledgeBaseDetail(id)
    const knowledge = response.data
    formState.topic = knowledge.topic || ''
    formState.title = knowledge.title || ''
    formState.type = knowledge.doc_type || knowledge.type || ''
    formState.content = knowledge.content || ''
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) {
    return
  }

  await formRef.value.validate()
  await updateKnowledgeBase(id, { ...formState })
  message.success('知识条目已提交重新入库')
  router.push('/knowledge/list')
}

onMounted(loadKnowledgeDetail)
</script>
