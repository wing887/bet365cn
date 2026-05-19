<template>
  <div class="login-page"><div class="login-card"><div class="login-logo">管理员</div><div class="login-form">
    <input v-model="username" class="input" placeholder="管理员账号" /><input v-model="password" type="password" class="input" placeholder="密码" />
    <button class="btn btn-primary btn-block" :disabled="loading" @click="login">{{ loading?'登录中...':'登录' }}</button>
    <div v-if="error" style="color:var(--red);font-size:12px;margin-top:8px;text-align:center;">{{ error }}</div>
  </div><router-link to="/login" style="display:block;text-align:center;margin-top:14px;font-size:12px;color:var(--b365-green);text-decoration:none;font-weight:600;">用户登录 →</router-link></div></div>
</template>
<script setup>import { ref, inject } from 'vue'; import { useRouter } from 'vue-router'; import { useAppStore } from '../stores/app'; const store = useAppStore(); const router = useRouter(); const showToast = inject('showToast'); const username = ref(''); const password = ref(''); const loading = ref(false); const error = ref(''); async function login(){loading.value=true;error.value='';try{await store.loginAdmin(username.value,password.value);showToast('管理员登录成功');router.push('/admin')}catch(e){error.value=e.response?.data?.error||'登录失败'}finally{loading.value=false}}</script>