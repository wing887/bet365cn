<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">金币统计</div>
    <div class="card" style="margin-bottom:8px;padding:12px;">
      <div style="display:flex;gap:6px;align-items:center;">
        <input type="date" v-model="dateFrom" class="input" style="flex:1;" />
        <span style="color:var(--text-muted);font-size:12px;">至</span>
        <input type="date" v-model="dateTo" class="input" style="flex:1;" />
        <button class="btn btn-primary btn-sm" @click="search">查询</button>
      </div>
    </div>
    <div class="summary-grid">
      <div class="summary-card"><div class="summary-value" style="color:var(--green-text);">+{{ totalAdd }}</div><div class="summary-label">总增加</div></div>
      <div class="summary-card"><div class="summary-value" style="color:var(--red);">{{ totalDeduct }}</div><div class="summary-label">总减少</div></div>
      <div class="summary-card"><div class="summary-value">{{ netChange }}</div><div class="summary-label">净变动</div></div>
      <div class="summary-card"><div class="summary-value">{{ adminOps.length }}</div><div class="summary-label">操作次数</div></div>
    </div>
    <div class="card"><div class="table-wrap"><table class="table">
      <thead><tr><th>时间</th><th>操作人</th><th>金额</th></tr></thead>
      <tbody><tr v-for="o in adminOps" :key="o.id">
        <td style="font-size:11px;color:var(--text-muted);">{{ o.created_at }}</td>
        <td>{{ o.admin_name }}</td>
        <td :style="{color:o.detail.includes('充值')?'var(--green-text)':'var(--red)',fontWeight:700}">{{ o.detail }}</td>
      </tr></tbody>
    </table></div></div>
  </div>
</template>
<script setup>import { ref, computed } from 'vue'; import { useAppStore } from '../stores/mockData'; const store = useAppStore(); const dateFrom = ref('2026-05-01'); const dateTo = ref('2026-05-19'); const adminOps = computed(()=>store.operationLogs.filter(l=>l.action.includes('金币'))); const totalAdd = computed(()=>adminOps.value.filter(o=>o.detail.includes('充值')).length*5000); const totalDeduct = computed(()=>adminOps.value.filter(o=>o.detail.includes('扣减')).length*3000); const netChange = computed(()=>totalAdd.value-totalDeduct.value); function search(){}</script>
