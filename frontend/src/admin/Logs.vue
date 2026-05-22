<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">操作日志</div>

    <div class="card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>时间</th>
              <th>操作人</th>
              <th>操作</th>
              <th>目标</th>
              <th>详情</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in store.operationLogs" :key="l.id">
              <td class="td-time">{{ store.fullDateTime(l.created_at) }}</td>
              <td>{{ l.admin_name }}</td>
              <td>{{ l.action }}</td>
              <td>{{ l.target_type }}{{ l.target_id ? '#' + l.target_id : '' }}</td>
              <td class="td-detail">{{ fmtDetail(l.detail) }}</td>
              <td class="td-time">{{ l.ip_address || '—' }}</td>
            </tr>
            <tr v-if="store.operationLogs.length === 0">
              <td colspan="6" class="empty-row">暂无日志</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()

function fmtDetail(d) {
  if (!d) return '—'
  if (typeof d !== 'object') return d
  // 金币操作：显示变更
  if (d.balance_before !== undefined && d.balance_after !== undefined) {
    return `${d.balance_before} → ${d.balance_after} (${d.amount > 0 ? '+' : ''}${d.amount})`
  }
  if (d.username && d.role) return `${d.username}(${d.role})`
  if (d.username) return d.username
  return JSON.stringify(d)
}

onMounted(async () => {
  await store.fetchLogs()
})
</script>
