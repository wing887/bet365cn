<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">金币操作</div>

    <!-- 代理余额显示 -->
    <div v-if="store.isAgent" class="card agent-balance-card">
      <span>我的代理余额：</span>
      <strong class="balance-value">{{ store.user?.coin_balance || 0 }}</strong>
      <span>金币</span>
      <span v-if="(store.user?.coin_balance || 0) === 0" class="hint">（请联系上级充值）</span>
    </div>

    <!-- 搜索用户 -->
    <div class="card search-card">
      <input
        v-model="searchQuery"
        type="text"
        class="input"
        placeholder="搜索用户名或昵称..."
        @input="onSearch"
      />
    </div>

    <!-- 操作表单 -->
    <div class="card form-card">
      <div class="form-title">
        {{ store.isAgent ? '给用户加金币' : '增减用户金币' }}
      </div>
      <div class="form-row">
        <select v-model="selectedUser" class="input select-user">
          <option value="">选择用户</option>
          <option v-for="u in store.adminUsers" :key="u.id" :value="u.id">
            {{ u.nickname }} ({{ u.username }}) — {{ u.coin_balance }}金币
          </option>
        </select>
        <input v-model.number="coinAmount" type="number" class="input" placeholder="金额" min="0" />
        <button class="btn btn-accent btn-sm" @click="doAdd">
          {{ store.isAgent ? '加金币' : '加金币' }}
        </button>
        <button v-if="!store.isAgent" class="btn btn-danger btn-sm" @click="doDeduct">减金币</button>
      </div>
      <div v-if="store.isAgent" class="form-hint">
        将从你的代理余额中扣除 {{ coinAmount || 0 }} 金币
      </div>
    </div>

    <!-- 用户余额列表 -->
    <div class="card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>昵称</th>
              <th>用户名</th>
              <th>当前金币</th>
              <th>最后登录</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in store.adminUsers" :key="u.id">
              <td>{{ u.nickname }}</td>
              <td>{{ u.username }}</td>
              <td class="td-coins">{{ u.coin_balance }}</td>
              <td class="td-time">{{ store.formatDate(u.last_login_at) }}</td>
              <td>
                <span :class="'tag ' + (u.status === 'active' ? 'tag-green' : 'tag-red')">
                  {{ u.status === 'active' ? '活跃' : '封禁' }}
                </span>
              </td>
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
const selectedUser = ref('')
const coinAmount = ref(0)
const searchQuery = ref('')
let searchTimer = null

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    await store.fetchAdminUsers(searchQuery.value)
  }, 300)
}

async function doAdd() {
  if (!selectedUser.value || coinAmount.value <= 0) {
    showToast('请选择用户并输入正数金额', 'error')
    return
  }
  try {
    const res = await store.modifyCoins(selectedUser.value, coinAmount.value)
    if (res.agent_balance !== undefined && store.user) {
      store.user.coin_balance = res.agent_balance
    }
    showToast(`成功加 ${coinAmount.value} 金币`)
    coinAmount.value = 0
    // 刷新列表更新余额
    await store.fetchAdminUsers(searchQuery.value)
  } catch (e) {
    showToast(e.response?.data?.error || '操作失败', 'error')
  }
}

async function doDeduct() {
  if (!selectedUser.value || coinAmount.value <= 0) {
    showToast('请选择用户并输入正数金额', 'error')
    return
  }
  try {
    await store.modifyCoins(selectedUser.value, -coinAmount.value)
    showToast(`成功扣减 ${coinAmount.value} 金币`)
    coinAmount.value = 0
    await store.fetchAdminUsers(searchQuery.value)
  } catch (e) {
    showToast(e.response?.data?.error || '操作失败', 'error')
  }
}

onMounted(async () => {
  await store.fetchAdminUsers()
})
</script>

<style scoped>
.search-card {
  padding: 12px;
  margin-bottom: 8px;
}
.search-card .input {
  width: 100%;
}
</style>
