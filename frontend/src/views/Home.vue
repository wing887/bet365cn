<template>
  <div>
    <div class="status-tabs" style="margin-top:6px;">
      <button v-for="t in tabs" :key="t.key" class="status-tab" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
    </div>
    <div v-if="store.loading" class="empty-state"><div class="empty-state-icon">⏳</div><div>加载中...</div></div>
    <div v-else-if="store.matches.length === 0" class="empty-state"><div class="empty-state-icon">📭</div><div>暂无比赛</div></div>
    <router-link v-for="m in store.matches" :key="m.id" :to="`/match/${m.id}`" class="match-card-link">
      <div class="match-card" :class="{ 'match-card-live': m.status === 'live', 'match-card-settled': m.status === 'settled' }">
        <div class="match-card-top"><span>{{ m.league_name }}</span><span><span v-if="m.status==='live'" class="live-indicator"></span><span :class="'tag '+(m.status==='live'?'tag-red':m.status==='pending'?'tag-orange':'tag-green')">{{ store.getMatchStatusText(m.status) }}</span></span></div>
        <div class="match-card-body">
          <div class="match-teams-row">
            <div class="match-team-col"><div class="match-team-name">{{ m.home_team }}</div></div>
            <div class="match-vs-area"><div v-if="m.status==='pending'" class="match-time-text">{{ store.formatMatchTime(m.match_date) }}</div><div v-else class="match-score-display">{{ m.scores_home }} - {{ m.scores_away }}</div><div v-if="m.status==='live'" style="font-size:10px;color:var(--red);">进行中</div></div>
            <div class="match-team-col"><div class="match-team-name">{{ m.away_team }}</div></div>
          </div>
          <div v-if="m.status==='pending'">
            <div style="font-size:11px;color:var(--text-muted);text-align:center;padding:6px 0;">点击查看赔率下注</div>
          </div>
        </div>
      </div>
    </router-link>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'; import { useAppStore } from '../stores/app'; const store = useAppStore()
const activeTab = ref('all')
const tabs = [{key:'all',label:'全部'},{key:'pending',label:'即将开始'},{key:'live',label:'进行中'},{key:'settled',label:'已结束'}]
async function switchTab(key) { activeTab.value = key; await store.fetchMatches(key === 'all' ? 'all' : key) }
onMounted(async () => { await store.fetchMatches('all') })
</script>