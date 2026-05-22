<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">用户管理</div>

    <!-- 搜索栏 -->
    <div class="card search-bar">
      <input
        v-model="searchQuery"
        class="input"
        placeholder="搜索用户名或昵称..."
        @keyup.enter="doSearch"
      />
      <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
    </div>

    <!-- 创建用户 -->
    <div v-if="store.canCreateAgent || store.isAgent" class="card form-card">
      <div class="form-title">创建用户</div>
      <div class="form-row">
        <input v-model="newUsername" class="input" placeholder="用户名" />
        <input v-model="newPassword" class="input" placeholder="密码" />
        <button class="btn btn-primary btn-sm" @click="createUser">创建</button>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>昵称</th>
              <th>金币</th>
              <th>最后登录</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in store.adminUsers" :key="u.id">
              <td class="td-username">{{ u.username }}</td>
              <td>{{ u.nickname }}</td>
              <td class="td-coins">{{ u.coin_balance }}</td>
              <td class="td-time">{{ store.formatDate(u.last_login_at) }}</td>
              <td>
                <span :class="'tag ' + (u.status === 'active' ? 'tag-green' : 'tag-red')">
                  {{ u.status === 'active' ? '活跃' : '封禁' }}
                </span>
              </td>
              <td>
                <div class="action-btns">
                  <button
                    v-if="u.status === 'active'"
                    class="btn btn-warn btn-xs"
                    @click="doBan(u.id, true)"
                  >封禁</button>
                  <button
                    v-if="u.status === 'disabled'"
                    class="btn btn-green btn-xs"
                    @click="doBan(u.id, false)"
                  >解封</button>
                  <button class="btn btn-danger btn-xs" @click="doDelete(u.id)">删除</button>
                </div>
              </td>
            </tr>
            <tr v-if="store.adminUsers.length === 0">
              <td colspan="6" class="empty-row">暂无用户</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const showToast = inject('showToast')
const searchQuery = ref('')
const newUsername = ref('')
const newPassword = ref('')

async function doSearch() {
  try {
    await store.fetchAdminUsers(searchQuery.value)
  } catch (e) {
    showToast('搜索失败', 'error')
  }
}

async function createUser() {
  if (!newUsername.value || !newPassword.value) {
    showToast('请填写账号和密码', 'error')
    return
  }
  try {
    await store.createUser(newUsername.value, newPassword.value)
    showToast('用户创建成功')
    newUsername.value = ''
    newPassword.value = ''
  } catch (e) {
    showToast(e.response?.data?.error || '创建失败', 'error')
  }
}

async function doBan(id, ban) {
  try {
    await store.banUser(id, ban)
    showToast(ban ? '用户已封禁' : '用户已解封')
  } catch (e) {
    showToast(e.response?.data?.error || '操作失败', 'error')
  }
}

async function doDelete(id) {
  if (!confirm('确定删除该用户？此操作不可恢复。')) return
  try {
    await store.deleteUser(id)
    showToast('用户已删除')
  } catch (e) {
    showToast(e.response?.data?.error || '删除失败', 'error')
  }
}

onMounted(async () => {
  await store.fetchAdminUsers()
})
</script>
