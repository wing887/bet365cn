<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">管理员管理</div>
    <div class="card" style="margin-bottom:8px;padding:12px;">
      <div style="font-weight:700;margin-bottom:8px;font-size:13px;">创建管理员</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;">
        <input v-model="newAdminUser" class="input" placeholder="账号" style="flex:1;min-width:100px;" />
        <input v-model="newAdminPwd" class="input" placeholder="密码" style="flex:1;min-width:100px;" />
        <button class="btn btn-primary btn-sm" @click="createAdmin">创建</button>
      </div>
    </div>
    <div class="card"><div class="table-wrap"><table class="table">
      <thead><tr><th>账号</th><th>角色</th><th>创建</th><th>操作</th></tr></thead>
      <tbody><tr v-for="a in store.adminAccounts" :key="a.id">
        <td style="font-weight:600;">{{ a.username }}</td>
        <td>{{ a.role==='super_admin'?'超级管理员':'普通管理员' }}</td>
        <td style="font-size:11px;color:var(--text-muted);">{{ a.created_at }}</td>
        <td><button v-if="a.role!=='super_admin'" class="btn btn-danger btn-xs" @click="deleteAdmin(a.id)">删除</button><span v-else style="font-size:11px;color:var(--text-muted);">—</span></td>
      </tr></tbody>
    </table></div></div>
  </div>
</template>
<script setup>import { ref, inject } from 'vue'; import { useAppStore } from '../stores/mockData'; const store = useAppStore(); const showToast = inject('showToast'); const newAdminUser = ref(''); const newAdminPwd = ref(''); function createAdmin(){if(!newAdminUser.value||!newAdminPwd.value){showToast('请填写账号密码','error');return}store.adminAccounts.push({id:Date.now(),username:newAdminUser.value,role:'admin',created_at:new Date().toISOString().slice(0,10)});showToast('管理员创建成功');newAdminUser.value='';newAdminPwd.value=''} function deleteAdmin(id){const i=store.adminAccounts.findIndex(a=>a.id===id);if(i>-1){store.adminAccounts.splice(i,1);showToast('管理员已删除')}}</script>
