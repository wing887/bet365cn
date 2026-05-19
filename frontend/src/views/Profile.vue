<template>
  <div>
    <div class="page-title">个人中心</div>
    <div class="card">
      <div style="text-align:center;padding:14px 0;">
        <div class="profile-avatar">U</div>
        <div style="font-size:18px;font-weight:800;margin-top:4px;">{{ store.user.nickname }}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">账号：{{ store.user.username }}</div>
        <div style="font-size:15px;color:var(--b365-green);font-weight:700;margin-top:6px;">🪙 {{ store.user.coin_balance }} 金币</div>
      </div>
    </div>
    <div class="card" style="margin-top:8px;">
      <div style="padding:12px 14px;">
        <div class="section-title" style="padding:0 0 8px 0;">修改密码</div>
        <input v-model="oldPwd" type="password" class="input" placeholder="原密码" style="margin-bottom:8px;" />
        <input v-model="newPwd" type="password" class="input" placeholder="新密码" style="margin-bottom:8px;" />
        <button class="btn btn-primary btn-block btn-sm" @click="changePwd">确认修改</button>
      </div>
    </div>
    <div style="padding:14px;text-align:center;">
      <button class="btn btn-outline btn-block" @click="logout">退出登录</button>
    </div>
  </div>
</template>
<script setup>import { ref, inject } from 'vue'; import { useRouter } from 'vue-router'; import { useAppStore } from '../stores/mockData'; const store = useAppStore(); const router = useRouter(); const showToast = inject('showToast'); const oldPwd = ref(''); const newPwd = ref(''); function changePwd() { if(!oldPwd.value||!newPwd.value){showToast('请填写密码','error');return} showToast('密码修改成功'); oldPwd.value=''; newPwd.value=''} function logout(){store.isLoggedIn=false;router.push('/login')}</script>
