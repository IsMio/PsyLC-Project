<template>
  <div class="page-shell">
    <a-card :bordered="false" class="glass-card">
      <div class="page-toolbar">
        <div>
          <p class="section-title">用户管理</p>
          <p class="section-desc">支持按用户名检索、编辑角色和维护用户头像信息。</p>
        </div>
        <div class="page-toolbar-right">
          <a-input
            v-model:value="searchKeyword"
            allow-clear
            size="large"
            class="search-input"
            placeholder="搜索用户名或显示名称"
            @pressEnter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
          <a-button size="large" @click="handleReset">重置</a-button>
          <a-button type="primary" size="large" @click="handleSearch">搜索</a-button>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="userList"
        :pagination="pagination"
        row-key="id"
        class="data-table"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'user'">
            <div class="user-cell">
              <a-avatar :src="record.avatar">{{ record.username?.slice(0, 1).toUpperCase() }}</a-avatar>
              <div>
                <div class="user-name">{{ record.username }}</div>
                <div class="user-meta">{{ record.display_name }}</div>
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'roles'">
            <a-space wrap>
              <a-tag v-for="role in record.roles" :key="role" :color="role === 'admin' ? 'gold' : 'blue'">
                {{ role === 'admin' ? '管理员' : '用户' }}
              </a-tag>
            </a-space>
          </template>

          <template v-else-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" @click="handleEdit(record)">编辑</a-button>
              <a-popconfirm title="确认删除这个用户吗？" ok-text="删除" cancel-text="取消" @confirm="handleDelete(record.id)">
                <a-button type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="editModalVisible"
      title="编辑用户"
      ok-text="保存"
      cancel-text="取消"
      @ok="handleEditOk"
    >
      <a-form ref="editFormRef" :model="editForm" :rules="editRules" layout="vertical">
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="editForm.username" disabled />
        </a-form-item>
        <a-form-item label="显示名称" name="display_name">
          <a-input v-model:value="editForm.display_name" placeholder="请输入显示名称" />
        </a-form-item>
        <a-form-item label="角色" name="roles">
          <a-select v-model:value="editForm.roles" mode="multiple" placeholder="选择角色">
            <a-select-option value="user">用户</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="头像地址" name="avatar">
          <a-input v-model:value="editForm.avatar" placeholder="请输入头像 URL" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { SearchOutlined } from '@ant-design/icons-vue'
import { deleteUser, getUserList, updateUser } from '../../api/admin'

interface UserItem {
  id: string
  username: string
  display_name: string
  roles: string[]
  avatar: string
  created_at: number
}

const searchKeyword = ref('')
const userList = ref<UserItem[]>([])
const loading = ref(false)
const editModalVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  userId: '',
  username: '',
  display_name: '',
  roles: [] as string[],
  avatar: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const editRules: Record<string, Rule[]> = {
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  roles: [{ required: true, type: 'array', min: 1, message: '请至少选择一个角色', trigger: 'change' }]
}

const columns = [
  { title: '用户', key: 'user' },
  { title: '角色', key: 'roles' },
  { title: '创建时间', key: 'created_at' },
  { title: '操作', key: 'action', width: 160 }
]

const loadUserList = async () => {
  loading.value = true
  try {
    const response = await getUserList({
      pageNum: pagination.current,
      pageSize: pagination.pageSize,
      keyword: searchKeyword.value
    })

    userList.value = response.data.rows || []
    pagination.total = response.data.total || 0
  } catch (error) {
    console.error('Load user list failed:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadUserList()
}

const handleReset = () => {
  searchKeyword.value = ''
  handleSearch()
}

const handleTableChange = (page: { current?: number; pageSize?: number }) => {
  pagination.current = page.current || 1
  pagination.pageSize = page.pageSize || 10
  loadUserList()
}

const handleEdit = (record: UserItem) => {
  editForm.userId = record.id
  editForm.username = record.username
  editForm.display_name = record.display_name
  editForm.roles = [...record.roles]
  editForm.avatar = record.avatar || ''
  editModalVisible.value = true
}

const handleEditOk = async () => {
  if (!editFormRef.value) {
    return
  }

  try {
    await editFormRef.value.validate()
    await updateUser({ ...editForm })
    message.success('用户信息已更新')
    editModalVisible.value = false
    loadUserList()
  } catch (error) {
    console.error('Edit user failed:', error)
  }
}

const handleDelete = async (id: string) => {
  try {
    await deleteUser(id)
    message.success('用户已删除')
    if (userList.value.length === 1 && pagination.current > 1) {
      pagination.current -= 1
    }
    loadUserList()
  } catch (error) {
    console.error('Delete user failed:', error)
  }
}

const formatDate = (timestamp: number) => new Date(timestamp * 1000).toLocaleString('zh-CN')

onMounted(loadUserList)
</script>

<style scoped>
.search-input {
  width: min(360px, 100%);
}

.data-table {
  margin-top: 20px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-weight: 700;
}

.user-meta {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>

