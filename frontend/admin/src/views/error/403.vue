<template>
  <div class="forbidden-page">
    <a-result
      status="403"
      title="403"
      sub-title="当前账号没有管理员权限，请联系系统管理员授权。"
    >
      <template #extra>
        <a-button type="primary" @click="$router.push('/login')">返回登录</a-button>
      </template>
    </a-result>
  </div>
</template>

<style scoped>
.forbidden-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
}
</style>
