<template>
  <div class="admin-page">
    <div class="admin-header">
      <div>
        <div class="page-title">
          {{ roleTitle }}
          <span v-if="store.isAgent" class="agent-balance">
            余额: <strong>{{ store.user?.coin_balance || 0 }}</strong> 金币
          </span>
        </div>
        <div class="admin-info">
          {{ store.user?.username }}
          <span class="role-tag" :class="'role-' + store.adminRole">{{ roleLabel }}</span>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-value">{{ adminUsersCount }}</div>
        <div class="summary-label">{{ store.isAgent ? '我的用户' : '用户总数' }}</div>
      </div>
      <div v-if="store.canSettle" class="summary-card">
        <div class="summary-value">{{ store.pendingSettlements.length }}</div>
        <div class="summary-label">待结算</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ store.matches.filter(m => m.status === 'pending').length }}</div>
        <div class="summary-label">今日赛事</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ store.myBets.length }}</div>
        <div class="summary-label">总下注</div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <div class="admin-nav">
      <router-link to="/admin/users" class="admin-nav-item">👥 用户管理</router-link>
      <router-link to="/admin/coins" class="admin-nav-item">💰 金币操作</router-link>
      <router-link v-if="store.canSettle" to="/admin/settlements" class="admin-nav-item">🏁 结算管理</router-link>
      <router-link v-if="!store.isAgent" to="/admin/agents" class="admin-nav-item">📈 代理管理</router-link>
      <router-link v-if="store.isAgent" to="/admin/customers" class="admin-nav-item">📊 客户统计</router-link>
      <router-link v-if="store.canCreateAgent" to="/admin/admins" class="admin-nav-item">🔑 管理员</router-link>
      <router-link to="/admin/logs" class="admin-nav-item">📋 操作日志</router-link>
      <router-link to="/admin/stats" class="admin-nav-item">📊 金币统计</router-link>
      <router-link v-if="store.isSuperAdmin" to="/admin/bet-limits" class="admin-nav-item">🎲 投注限额</router-link>
      <router-link v-if="store.isSuperAdmin" to="/admin/market-status" class="admin-nav-item">🚫 封盘管理</router-link>
      <router-link to="/admin/match-bets" class="admin-nav-item">📋 下注核对</router-link>
    </div>

    <!-- 待结算提醒（仅超管） -->
    <div v-if="store.canSettle && store.pendingSettlements.length > 0" class="section-title">待结算提醒</div>
    <div v-if="store.canSettle" v-for="s in store.pendingSettlements" :key="s.match_id" class="card settlement-card-mini">
      <div class="settlement-row">
        <div>
          <div class="settlement-match-name">{{ s.home_team }} {{ s.scores_home }}:{{ s.scores_away }} {{ s.away_team }}</div>
          <div class="settlement-meta">{{ s.league_name }}</div>
        </div>
        <span class="tag tag-orange">待结算</span>
      </div>
      <div class="settlement-stats-row">{{ s.total_bets }}注 · {{ s.total_users }}用户 · {{ s.total_payout }}金币</div>
    </div>

    <div class="logout-wrap">
      <button class="btn btn-outline btn-sm" @click="logout">退出管理后台</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()
const showToast = inject('showToast')
const adminUsersCount = ref(0)

const roleTitle = computed(() => {
  if (store.isSuperAdmin) return '超级管理员后台'
  if (store.isAdmin) return '管理员后台'
  return '代理后台'
})

const roleLabel = computed(() => {
  if (store.isSuperAdmin) return '超管'
  if (store.isAdmin) return '管理'
  return '代理'
})

function logout() {
  store.logout()
  router.push('/admin/login')
}

onMounted(async () => {
  try {
    const data = await store.fetchAdminUsers()
    adminUsersCount.value = data.users?.length || 0
  } catch (e) { /* ignore */ }
  if (store.canSettle) {
    await store.fetchPendingSettlements()
  }
})
</script>
