<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-left">
        <span class="logo">bet<span class="logo-highlight">365</span>cn</span>
      </div>
      <div class="header-right">
        <template v-if="store.isLoggedIn && store.user">
          <span class="coin-badge">🪙 {{ store.user.coin_balance }}</span>
          <span class="nickname">{{ store.user.nickname }}</span>
        </template>
        <template v-else-if="store.isAdminLoggedIn && store.user">
          <span class="coin-badge">{{ store.isSuperAdmin ? '超管' : '管理员' }}</span>
          <span class="nickname">{{ store.user.username }}</span>
        </template>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>

    <nav v-if="showBottomNav" class="bottom-nav">
      <router-link to="/" class="nav-item" exact-active-class="active">
        <span class="nav-icon">⚽</span><span>首页</span>
      </router-link>
      <router-link to="/my-bets" class="nav-item" active-class="active">
        <span class="nav-icon">📋</span><span>下注</span>
      </router-link>
      <router-link to="/my-coins" class="nav-item" active-class="active">
        <span class="nav-icon">💰</span><span>金币</span>
      </router-link>
      <router-link to="/profile" class="nav-item" active-class="active">
        <span class="nav-icon">👤</span><span>我的</span>
      </router-link>
    </nav>

    <div v-if="toast.show" class="toast" :class="toast.type">{{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { computed, ref, provide, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from './stores/app'
const store = useAppStore()
const route = useRoute()

const showBottomNav = computed(() => !route.path.startsWith('/admin') && route.path !== '/login')

const toast = ref({ show: false, msg: '', type: 'success' })
function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  setTimeout(() => { toast.value.show = false }, 2000)
}

provide('showToast', showToast)
provide('store', store)

onMounted(async () => {
  store.restoreSession()
  if (store.isLoggedIn) {
    store.fetchProfile().catch(() => {})
  }
})
</script>
