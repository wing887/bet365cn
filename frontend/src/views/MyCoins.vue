<template>
  <div><div class="page-title">金币记录</div>
    <div class="summary-grid"><div class="summary-card"><div class="summary-value">{{ store.user?.coin_balance||0 }}</div><div class="summary-label">当前余额</div></div><div class="summary-card"><div class="summary-value">{{ totalIn }}</div><div class="summary-label">累计充值</div></div></div>
    <div class="card"><div v-for="tx in store.transactions" :key="tx.id" class="tx-item"><div class="tx-left"><div class="tx-note">{{ tx.note }}</div><div class="tx-time">{{ store.formatDate(tx.created_at) }}</div></div><div :class="tx.amount>=0?'tx-positive':'tx-negative'">{{ tx.amount>=0?'+':'' }}{{ tx.amount }}</div></div></div>
  </div>
</template>
<script setup>import { computed, onMounted } from 'vue'; import { useAppStore } from '../stores/app'; const store = useAppStore(); const totalIn = computed(()=>store.transactions.filter(t=>t.amount>0).reduce((s,t)=>s+t.amount,0)); onMounted(async()=>{await store.fetchTransactions()})</script>