<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">bet<span>365</span>cn</div>
      <div class="login-form">
        <input v-model="username" class="input" placeholder="用户名" />
        <input v-model="password" type="password" class="input" placeholder="密码" />
        <button class="btn btn-primary btn-block" :disabled="loading" @click="login">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <div v-if="error" style="color:var(--red);font-size:12px;margin-top:8px;text-align:center;">{{ error }}</div>
      </div>
      <div style="text-align:center;margin-top:14px;font-size:11px;color:var(--text-muted);">模拟网站，账号由管理员创建</div>
      <router-link to="/admin/login" style="display:block;text-align:center;margin-top:10px;font-size:12px;color:var(--b365-green);text-decoration:none;font-weight:600;">管理员登录 →</router-link>
    </div>
  </div>
</template>
<script setup>
import { ref, inject } from 'vue'; import { useRouter } from 'vue-router'; import { useAppStore } from '../stores/app'
const store = useAppStore(); const router = useRouter(); const showToast = inject('showToast')
const username = ref(''); const password = ref(''); const loading = ref(false); const error = ref('')
async function login() {
  if (!username.value || !password.value) { error.value = '请输入账号和密码'; return }
  loading.value = true; error.value = ''
  try {
    await store.loginUser(username.value, password.value)
    showToast('登录成功'); router.push('/')
  } catch (e) { error.value = e.response?.data?.error || '登录失败' }
  finally { loading.value = false }
}
</script>