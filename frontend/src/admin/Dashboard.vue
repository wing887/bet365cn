<template>
  <div class="admin-page">
    <div class="page-title">管理后台</div>
    <div class="summary-grid">
      <div class="summary-card"><div class="summary-value">{{ store.adminUsers.length }}</div><div class="summary-label">用户总数</div></div>
      <div class="summary-card"><div class="summary-value">{{ store.pendingSettlements.length }}</div><div class="summary-label">待结算</div></div>
      <div class="summary-card"><div class="summary-value">{{ store.matches.filter(m=>m.status==='pending').length }}</div><div class="summary-label">今日赛事</div></div>
      <div class="summary-card"><div class="summary-value">{{ store.myBets.length }}</div><div class="summary-label">总下注</div></div>
    </div>
    <div class="admin-nav">
      <router-link to="/admin/users" class="admin-nav-item">👥 用户管理</router-link>
      <router-link to="/admin/coins" class="admin-nav-item">💰 金币操作</router-link>
      <router-link v-if="store.isSuperAdmin" to="/admin/settlements" class="admin-nav-item">🏁 结算管理</router-link>
      <router-link v-if="store.isSuperAdmin" to="/admin/admins" class="admin-nav-item">🔑 管理员</router-link>
      <router-link v-if="store.isSuperAdmin" to="/admin/logs" class="admin-nav-item">📋 操作日志</router-link>
      <router-link v-if="store.isSuperAdmin" to="/admin/stats" class="admin-nav-item">📊 金币统计</router-link>
    </div>
    <div v-if="store.isSuperAdmin" class="section-title">待结算提醒</div>
    <div v-if="store.isSuperAdmin && store.pendingSettlements.length > 0">
      <div v-for="s in store.pendingSettlements" :key="s.id" class="card" style="padding:10px 14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-weight:700;">{{ s.match_home }} {{ s.scores }} {{ s.match_away }}</span>
          <span class="tag tag-orange">待结算</span>
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">{{ s.total_bets }}注 · {{ s.total_payout }}金币</div>
      </div>
    </div>
    <div style="padding:14px;text-align:center;">
      <button class="btn btn-outline btn-sm" @click="logout">退出管理后台</button>
    </div>
  </div>
</template>
<script setup>import { useRouter } from 'vue-router'; import { useAppStore } from '../stores/mockData'; const store = useAppStore(); const router = useRouter(); function logout(){store.isAdminLoggedIn=false;store.isSuperAdmin=false;router.push('/admin/login')}</script>
