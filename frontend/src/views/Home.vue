<template>
  <div>
    <div class="status-tabs" style="margin-top:6px;">
      <button v-for="t in tabs" :key="t.key" class="status-tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        {{ t.label }}
      </button>
    </div>

    <div v-if="filteredMatches.length === 0" class="empty-state">
      <div class="empty-state-icon">📭</div>
      <div>暂无比赛</div>
    </div>

    <router-link
      v-for="m in filteredMatches" :key="m.id" :to="`/match/${m.id}`"
      class="match-card-link"
    >
      <div class="match-card" :class="{ 'match-card-live': m.status === 'live', 'match-card-settled': m.status === 'settled' }">
        <div class="match-card-top">
          <span>{{ m.league_name }}</span>
          <span>
            <span v-if="m.status === 'live'" class="live-indicator"></span>
            <span :class="'tag ' + (m.status === 'live' ? 'tag-red' : m.status === 'pending' ? 'tag-orange' : 'tag-green')">{{ store.getMatchStatusText(m.status) }}</span>
          </span>
        </div>
        <div class="match-card-body">
          <div class="match-teams-row">
            <div class="match-team-col">
              <div class="match-team-name">{{ m.home_team }}</div>
            </div>
            <div class="match-vs-area">
              <div v-if="m.status === 'pending'" class="match-time-text">{{ store.formatMatchTime(m.match_date) }}</div>
              <div v-else class="match-score-display">{{ m.scores_home }} - {{ m.scores_away }}</div>
              <div v-if="m.status === 'live'" style="font-size:10px;color:var(--red);">进行中</div>
            </div>
            <div class="match-team-col">
              <div class="match-team-name">{{ m.away_team }}</div>
            </div>
          </div>
          <div v-if="m.status === 'pending' && store.getOdds(m.id)" class="odds-btns-row">
            <div class="odds-btn-b365">
              <span class="odds-btn-label">主胜</span>
              <span class="odds-btn-value">{{ store.getOdds(m.id).ML.home }}</span>
            </div>
            <div class="odds-btn-b365">
              <span class="odds-btn-label">平局</span>
              <span class="odds-btn-value">{{ store.getOdds(m.id).ML.draw }}</span>
            </div>
            <div class="odds-btn-b365">
              <span class="odds-btn-label">客胜</span>
              <span class="odds-btn-value">{{ store.getOdds(m.id).ML.away }}</span>
            </div>
          </div>
        </div>
      </div>
    </router-link>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAppStore } from '../stores/mockData'
const store = useAppStore()
const activeTab = ref('all')
const tabs = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '即将开始' },
  { key: 'live', label: '进行中' },
  { key: 'settled', label: '已结束' },
]
const filteredMatches = computed(() => {
  if (activeTab.value === 'all') return store.matches
  return store.matches.filter(m => m.status === activeTab.value)
})
</script>
