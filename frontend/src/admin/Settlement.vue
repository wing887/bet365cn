<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">结算管理</div>
    <div v-if="store.pendingSettlements.length===0" class="empty-state"><div class="empty-state-icon">🏁</div><div>暂无待结算比赛</div></div>
    <div v-for="s in store.pendingSettlements" :key="s.id" class="settlement-card">
      <div class="settlement-hd">
        <div><div class="settlement-match-name">{{ s.match_home }} vs {{ s.match_away }}</div><div style="font-size:10px;color:var(--text-muted);">{{ s.league }}</div></div>
        <div class="settlement-score-big">{{ s.scores }}</div>
      </div>
      <div class="settlement-stats">
        <div><strong>{{ s.total_bets }}</strong>下注总数</div>
        <div><strong>{{ s.total_users }}</strong>参与用户</div>
        <div><strong style="color:var(--green-text);">{{ s.total_payout }}</strong>总赔付</div>
      </div>
      <div class="settlement-actions">
        <button class="btn btn-primary" @click="confirmSettle(s.id)">确认结算</button>
        <button class="btn btn-outline" @click="cancelMatch(s.id)">取消比赛</button>
      </div>
    </div>
    <div class="section-title" style="margin-top:8px;">已结算</div>
    <div class="card" style="padding:10px 14px;">
      <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border-light);"><div><div style="font-weight:700;">皇家马德里 3:1 巴塞罗那</div><div style="font-size:10px;color:var(--text-muted);">西甲 · 15注/12用户</div></div><span class="tag tag-green">已结算</span></div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;"><div><div style="font-weight:700;">AC米兰 2:2 那不勒斯</div><div style="font-size:10px;color:var(--text-muted);">意甲 · 8注/6用户</div></div><span class="tag tag-green">已结算</span></div>
    </div>
  </div>
</template>
<script setup>import { inject } from 'vue'; import { useAppStore } from '../stores/mockData'; const store = useAppStore(); const showToast = inject('showToast'); function confirmSettle(id){const i=store.pendingSettlements.findIndex(s=>s.id===id);if(i>-1){store.pendingSettlements.splice(i,1);showToast('结算成功，金币已发放')}} function cancelMatch(id){const i=store.pendingSettlements.findIndex(s=>s.id===id);if(i>-1){store.pendingSettlements.splice(i,1);showToast('比赛已取消，金币已退回')}}</script>
