<template>
  <div class="page-shell">
    <a-card :bordered="false" class="glass-card">
      <template #title>
        <p class="section-title">输出过滤策略</p>
        <p class="section-desc">管理员可维护规则表达式与替换模板，统一控制心理咨询输出过滤行为。</p>
      </template>

      <a-form layout="vertical">
        <a-space size="large" class="switch-row">
          <a-switch v-model:checked="policy.enabled" checked-children="启用过滤" un-checked-children="关闭过滤" />
          <a-switch v-model:checked="policy.review_enabled" checked-children="启用二次审查" un-checked-children="关闭二次审查" />
        </a-space>

        <div class="section-block">
          <div class="section-header">
            <div class="section-subtitle">规则列表</div>
            <a-button type="dashed" @click="handleAddRule">新增规则</a-button>
          </div>
          <a-table :data-source="policy.rules" :pagination="false" row-key="reason" size="small">
            <a-table-column title="原因" key="reason" width="180">
              <template #default="{ record }">
                <a-input v-model:value="record.reason" placeholder="如 medical_diagnosis" />
              </template>
            </a-table-column>
            <a-table-column title="正则模式" key="pattern">
              <template #default="{ record }">
                <a-input v-model:value="record.pattern" placeholder="输入触发正则" />
              </template>
            </a-table-column>
            <a-table-column title="启用" key="enabled" width="100">
              <template #default="{ record }">
                <a-switch v-model:checked="record.enabled" />
              </template>
            </a-table-column>
            <a-table-column title="操作" key="action" width="100">
              <template #default="{ index }">
                <a-button type="link" danger @click="handleDeleteRule(index)">删除</a-button>
              </template>
            </a-table-column>
          </a-table>
        </div>

        <div class="section-block">
          <div class="section-subtitle">替换模板</div>
          <div v-for="(value, key) in policy.templates" :key="key" class="template-item">
            <label>{{ key }}</label>
            <a-textarea v-model:value="policy.templates[key]" :rows="4" />
          </div>
        </div>

        <a-space>
          <a-button type="primary" @click="handleSave">保存策略</a-button>
          <a-button @click="loadPolicy">刷新</a-button>
        </a-space>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { getOutputFilterPolicy, updateOutputFilterPolicy, type OutputFilterPolicy } from '../../api/admin'

const policy = reactive<OutputFilterPolicy>({
  enabled: true,
  review_enabled: true,
  rules: [],
  templates: {}
})

const loadPolicy = async () => {
  const response = await getOutputFilterPolicy()
  const data = response.data
  policy.enabled = Boolean(data.enabled)
  policy.review_enabled = Boolean(data.review_enabled)
  policy.rules = data.rules || []
  policy.templates = data.templates || {}
}

const handleAddRule = () => {
  policy.rules.push({
    reason: '',
    pattern: '',
    enabled: true
  })
}

const handleDeleteRule = (index: number) => {
  policy.rules.splice(index, 1)
}

const handleSave = async () => {
  await updateOutputFilterPolicy({
    enabled: Boolean(policy.enabled),
    review_enabled: Boolean(policy.review_enabled),
    rules: policy.rules
      .map((item) => ({
        reason: String(item.reason || '').trim(),
        pattern: String(item.pattern || '').trim(),
        enabled: Boolean(item.enabled)
      }))
      .filter((item) => item.reason && item.pattern),
    templates: { ...policy.templates }
  })
  message.success('输出过滤策略已保存')
  loadPolicy()
}

onMounted(loadPolicy)
</script>

<style scoped>
.switch-row {
  margin-bottom: 20px;
}

.section-block {
  margin-bottom: 24px;
}

.section-subtitle {
  font-weight: 700;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.template-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
</style>
