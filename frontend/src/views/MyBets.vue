<template>
  <div><div class="page-title">我的下注</div>
    <div class="card" v-if="store.myBets.length===0"><div class="empty-state"><div class="empty-state-icon">📋</div><div>暂无下注记录</div></div></div>
    <div class="card" v-else><div v-for="b in store.myBets" :key="b.id" class="bet-item">
      <div class="bet-match-title">{{ b.match_home }} vs {{ b.match_away }}</div>
      <div class="bet-detail-line"><span>{{ b.league_name }}</span><span>{{ store.getMarketName(b.market_type) }}</span><span>{{ store.getSelectionLabel(b.market_type, b.selection) }}</span></div>
      <div class="bet-bottom-row"><span class="bet-amount-text">{{ b.bet_amount }} 金币 @{{ b.odds_value }}</span><span v-if="b.status==='won'" class="bet-result-won">+{{ b.potential_win }}</span><span v-else-if="b.status==='lost'" class="bet-result-lost">-{{ b.bet_amount }}</span><span v-else class="bet-result-pending">待结算</span></div>
      <div v-if="b.settled_at" style="font-size:10px;color:var(--text-muted);margin-top:2px;">{{ store.formatDate(b.settled_at) }}</div>
    </div></div>
  </div>
</template>
<script setup>import { onMounted } from 'vue'; import { useAppStore } from '../stores/app'; const store = useAppStore(); onMounted(async()=>{await store.fetchMyBets()})</script>