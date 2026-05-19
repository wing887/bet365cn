<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">操作日志</div>
    <div class="card"><div class="table-wrap"><table class="table">
      <thead><tr><th>时间</th><th>操作人</th><th>操作</th><th>目标</th><th>详情</th></tr></thead>
      <tbody><tr v-for="l in store.operationLogs" :key="l.id">
        <td style="font-size:11px;color:var(--text-muted);white-space:nowrap;">{{ l.created_at }}</td>
        <td>{{ l.admin_name }}</td><td>{{ l.action }}</td><td>{{ l.target }}</td>
        <td style="font-size:12px;">{{ l.detail }}</td>
      </tr></tbody>
    </table></div></div>
  </div>
</template>
<script setup>import { useAppStore } from '../stores/mockData'; const store = useAppStore()</script>
