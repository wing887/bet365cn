<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">bet<span>365</span>cn</div>
      <div class="login-form">
        <input v-model="username" class="input" placeholder="用户名" />
        <input v-model="password" type="password" class="input" placeholder="密码" />
        <button class="btn btn-primary btn-block" @click="login">登录</button>
      </div>
      <div style="text-align:center;margin-top:14px;font-size:11px;color:var(--text-muted);">模拟网站，账号由管理员创建</div>
    </div>
  </div>
</template>
<script setup>import { ref, inject } from 'vue'; import { useRouter } from 'vue-router'; import { useAppStore } from '../stores/mockData'; const store = useAppStore(); const router = useRouter(); const showToast = inject('showToast'); const username = ref('user001'); const password = ref('password'); function login() { store.isLoggedIn = true; store.user.username = username.value; store.user.nickname = username.value; showToast('登录成功'); router.push('/') }</script>
