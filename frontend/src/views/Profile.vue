<template>
  <div>
    <div class="score_board"><div class="score_league">个人中心</div></div>
    <div class="acc_user" style="display:flex;flex-direction:column;align-items:center;padding:20px;" v-if="store.user">
      <div style="font-size:18px;font-weight:700;">{{ store.user.nickname }}</div>
      <div style="font-size:24px;font-weight:900;color:var(--gold);margin-top:4px;">🪙 {{ store.user.coin_balance }} 金币</div>
    </div>
    <div class="acc_menu">
      <div class="acc_item" @click="router.push('/my-bets')">投注记录</div>
      <div class="acc_item" @click="router.push('/my-coins')">金币记录</div>
      <div class="acc_item" @click="logout">退出登录</div>
    </div>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
const router = useRouter()
const store = useAppStore()
function logout() { store.logout(); router.push('/login') }
</script>
