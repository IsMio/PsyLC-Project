<template>
  <div class="page-shell">
    <a-card :bordered="false" class="glass-card">
      <template #title>
        <p class="section-title">系统配置</p>
        <p class="section-desc">只允许编辑白名单配置项，避免直接裸改 `config.yaml`。保存后可由管理员确认触发重启。</p>
      </template>

      <a-form layout="vertical">
        <div class="config-grid">
          <a-form-item label="模型名称">
            <a-input v-model:value="form.dashscope.model_name" />
          </a-form-item>
          <a-form-item label="模型最大 Token">
            <a-input-number v-model:value="form.dashscope.model_max_tokens" class="full-width" />
          </a-form-item>
          <a-form-item label="Embedding 模型">
            <a-input v-model:value="form.dashscope.embeddings_model_name" />
          </a-form-item>
          <a-form-item label="温度">
            <a-input-number v-model:value="form.model.temperature" :step="0.1" class="full-width" />
          </a-form-item>
          <a-form-item label="Top P">
            <a-input-number v-model:value="form.model.top_p" :step="0.1" class="full-width" />
          </a-form-item>
          <a-form-item label="启用联网搜索">
            <a-switch v-model:checked="form.model.enable_search" />
          </a-form-item>
          <a-form-item label="Chroma 集合名">
            <a-input v-model:value="form.app.chroma_collection_name" />
          </a-form-item>
          <a-form-item label="Chroma 存储目录">
            <a-input v-model:value="form.app.chroma_persist_dir" />
          </a-form-item>
          <a-form-item label="Prompt 模板路径">
            <a-input v-model:value="form.app.prompt_template_path" />
          </a-form-item>
          <a-form-item label="最大历史消息数">
            <a-input-number v-model:value="form.app.max_history_messages" class="full-width" />
          </a-form-item>
          <a-form-item label="最大历史字符数">
            <a-input-number v-model:value="form.app.max_history_chars" class="full-width" />
          </a-form-item>
          <a-form-item label="单条消息最大字符数">
            <a-input-number v-model:value="form.app.max_single_message_chars" class="full-width" />
          </a-form-item>
          <a-form-item label="输出过滤开关">
            <a-switch v-model:checked="form.app.output_filter_enabled" />
          </a-form-item>
          <a-form-item label="二次审查开关">
            <a-switch v-model:checked="form.app.output_filter_review_enabled" />
          </a-form-item>
          <a-form-item label="MinerU API Base URL">
            <a-input v-model:value="form.app.mineru_base_url" placeholder="如 https://mineru.net/api/kie" />
          </a-form-item>
          <a-form-item label="MinerU Pipeline ID">
            <a-input v-model:value="form.app.mineru_pipeline_id" />
          </a-form-item>
          <a-form-item label="MinerU 超时秒数">
            <a-input-number v-model:value="form.app.mineru_timeout" class="full-width" />
          </a-form-item>
          <a-form-item label="数据库路径">
            <a-input v-model:value="form.db.path" />
          </a-form-item>
          <a-form-item label="Redis Host">
            <a-input v-model:value="form.redis.redis_host" />
          </a-form-item>
          <a-form-item label="Redis Port">
            <a-input-number v-model:value="form.redis.redis_port" class="full-width" />
          </a-form-item>
          <a-form-item label="Redis DB">
            <a-input-number v-model:value="form.redis.redis_db" class="full-width" />
          </a-form-item>
          <a-form-item label="JWT 算法">
            <a-input v-model:value="form.jwt.algorithm" />
          </a-form-item>
          <a-form-item label="Token 过期分钟数">
            <a-input-number v-model:value="form.jwt.access_token_expire_minutes" class="full-width" />
          </a-form-item>
        </div>

        <a-form-item label="系统提示词">
          <a-textarea v-model:value="form.app.system_prompt" :rows="10" />
        </a-form-item>

        <a-divider>MinerU 分割预览</a-divider>
        <a-form-item label="上传文件预览分割效果">
          <input type="file" accept=".pdf,.txt,.md,.csv,.json" @change="handlePreviewFileChange" />
          <div class="hint-text">预览将优先使用 MinerU 返回的结构化段落；若无结构化结果，则展示回退结果。</div>
        </a-form-item>
        <a-space>
          <a-button :disabled="!previewFile" @click="handlePreviewChunks">预览分割</a-button>
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

        <a-space>
          <a-button type="primary" @click="handleSave">保存白名单配置</a-button>
          <a-button @click="loadConfig">刷新</a-button>
          <a-popconfirm
            title="确认已完成配置保存并准备重启系统？"
            ok-text="确认重启"
            cancel-text="取消"
            @confirm="handleRestart"
          >
            <a-button danger>确认后重启系统</a-button>
          </a-popconfirm>
        </a-space>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { getSystemConfig, previewMineruChunks, restartSystem, updateSystemConfig } from '../../api/admin'

const form = reactive<any>({
  dashscope: {},
  model: {},
  app: {},
  db: {},
  redis: {},
  jwt: {}
})
const previewFile = ref<File | null>(null)
const previewResult = ref<{ chunks: string[]; count: number; used_structured_blocks: boolean } | null>(null)

const assignSection = (target: any, source: any = {}) => {
  Object.keys(target).forEach((key) => delete target[key])
  Object.assign(target, source)
}

const loadConfig = async () => {
  const response = await getSystemConfig()
  const data = response.data || {}
  assignSection(form.dashscope, data.dashscope)
  assignSection(form.model, data.model)
  assignSection(form.app, data.app)
  assignSection(form.db, data.db)
  assignSection(form.redis, data.redis)
  assignSection(form.jwt, data.jwt)
}

const handleSave = async () => {
  await updateSystemConfig({
    dashscope: { ...form.dashscope },
    model: { ...form.model },
    app: { ...form.app },
    db: { ...form.db },
    redis: { ...form.redis },
    jwt: { ...form.jwt }
  })
  message.success('白名单配置已保存，请确认后再重启系统')
  loadConfig()
}

const handlePreviewFileChange = (event: Event) => {
  previewFile.value = (event.target as HTMLInputElement).files?.[0] || null
}

const handlePreviewChunks = async () => {
  if (!previewFile.value) {
    message.error('请先选择文件')
    return
  }
  const data = new FormData()
  data.append('file', previewFile.value)
  const response = await previewMineruChunks(data)
  previewResult.value = response.data
}

const handleRestart = async () => {
  await restartSystem()
  message.success('重启请求已发送，请按部署流程确认服务状态')
}

onMounted(loadConfig)
</script>

<style scoped>
.config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.full-width {
  width: 100%;
}

.hint-text {
  margin-top: 8px;
  color: var(--text-secondary);
}

.preview-alert {
  margin-top: 16px;
}

.preview-list {
  margin: 16px 0 20px;
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

@media (max-width: 900px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
}
</style>
