<template>
  <div class="admin-page"><router-link to="/admin" class="back-link">← 返回后台</router-link><div class="page-title">结算管理</div>
    <div v-if="store.pendingSettlements.length===0" class="empty-state"><div class="empty-state-icon">🏁</div><div>暂无待结算比赛</div></div>
    <div v-for="s in store.pendingSettlements" :key="s.match_id" class="settlement-card">
      <div class="settlement-hd"><div><div class="settlement-match-name">{{ s.home_team }} vs {{ s.away_team }}</div><div style="font-size:10px;color:var(--text-muted);">{{ s.league_name }}</div></div><div class="settlement-score-big">{{ s.scores_home }} : {{ s.scores_away }}</div></div>
      <div class="settlement-stats"><div><strong>{{ s.total_bets }}</strong>下注</div><div><strong>{{ s.total_users }}</strong>用户</div><div><strong style="color:var(--green-text);">{{ s.total_payout }}</strong>赔付</div></div>
      <div class="settlement-actions"><button class="btn btn-primary" @click="doConfirm(s.match_id)">确认结算</button><button class="btn btn-outline" @click="doCancel(s.match_id)">取消比赛</button></div>
    </div>
  </div>
</template>
<script setup>import { inject, onMounted } from 'vue'; import { useAppStore } from '../stores/app'; const store = useAppStore(); const showToast = inject('showToast'); async function doConfirm(id){try{await store.confirmSettlement(id);showToast('结算成功')}catch(e){showToast(e.response?.data?.error||'结算失败','error')}} async function doCancel(id){try{await store.cancelMatch(id);showToast('比赛已取消，金币已退回')}catch(e){showToast(e.response?.data?.error||'取消失败','error')}}; onMounted(async()=>{await store.fetchPendingSettlements()})</script>