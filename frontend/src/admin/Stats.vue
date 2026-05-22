<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">金币统计</div>

    <div class="card form-card">
      <div class="form-row">
        <input type="date" v-model="dateFrom" class="input" />
        <span class="date-sep">至</span>
        <input type="date" v-model="dateTo" class="input" />
        <button class="btn btn-primary btn-sm" @click="doSearch">查询</button>
      </div>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-value green">+{{ stats.total_add }}</div>
        <div class="summary-label">总增加</div>
      </div>
      <div class="summary-card">
        <div class="summary-value red">-{{ stats.total_deduct }}</div>
        <div class="summary-label">总减少</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ stats.net }}</div>
        <div class="summary-label">净变动</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ stats.total_ops }}</div>
        <div class="summary-label">操作次数</div>
      </div>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>操作人</th>
              <th>增加</th>
              <th>扣减</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in (stats.by_admin || [])" :key="a.admin_id">
              <td>{{ a.admin_name }}</td>
              <td class="td-coins green">+{{ a.add }}</td>
              <td class="td-coins red">-{{ a.deduct }}</td>
            </tr>
            <tr v-if="(stats.by_admin || []).length === 0">
              <td colspan="3" class="empty-row">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const showToast = inject('showToast')

const today = new Date()
const dateFrom = ref(new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10))
const dateTo = ref(today.toISOString().slice(0, 10))

const stats = reactive({ total_add: 0, total_deduct: 0, net: 0, total_ops: 0, by_admin: [] })

async function doSearch() {
  try {
    const r = await store.fetchStats(dateFrom.value, dateTo.value)
    Object.assign(stats, r)
  } catch (e) {
    showToast('查询失败', 'error')
  }
}
</script>
