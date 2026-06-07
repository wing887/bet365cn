<template>
  <div>
    <!-- 联赛筛选 -->
    <div class="league-filter">
      <button
        v-for="lg in leagues"
        :key="lg.slug"
        class="league-btn"
        :class="{ active: selectedLeagues.includes(lg.slug), disabled: lg.disabled, highlight: lg.highlight }"
        :disabled="lg.disabled"
        @click="toggleLeague(lg.slug)"
      >{{ lg.label }}</button>
    </div>

    <!-- 状态标签 -->
    <div class="status-tabs">
      <button v-for="t in tabs" :key="t.key" class="status-tab" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
    </div>

    <div v-if="store.loading" class="empty-state"><div class="empty-state-icon">⏳</div><div>加载中...</div></div>
    <div v-else-if="store.matches.length === 0" class="empty-state"><div class="empty-state-icon">📭</div><div>暂无比赛</div></div>

    <router-link v-for="m in store.matches" :key="m.id" :to="`/match/${m.id}`" class="match-card-link">
      <div class="match-card" :class="{
        'match-card-live': m.status === 'live',
        'match-card-settled': m.status === 'settled',
        'match-card-has-odds': m.has_odds,
        'match-card-no-odds': m.status === 'pending' && !m.has_odds
      }">
        <div class="match-card-top">
          <span class="match-league-name">{{ m.league_name_cn || m.league_name }}</span>
          <span class="match-card-top-right">
            <span v-if="m.status === 'pending' && m.has_odds" class="odds-badge odds-badge-yes">有赔率</span>
            <span v-else-if="m.status === 'pending' && !m.has_odds" class="odds-badge odds-badge-no">等待赔率</span>
            <span v-if="m.status==='live'" class="live-indicator"></span>
            <span :class="'tag '+(m.status==='live'?'tag-red':m.status==='pending'?'tag-orange':'tag-green')">{{ store.getMatchStatusText(m.status) }}</span>
          </span>
        </div>
        <div class="match-card-body">
          <div class="match-teams-row">
            <div class="match-team-col">
              <img v-if="m.home_logo_id" :src="`${logoBase}/${m.home_logo_id}.png`" class="team-logo" />
              <div v-else class="team-logo-fallback">{{ m.home_team.charAt(0) }}</div>
              <div class="match-team-name">{{ m.home_team }}</div>
            </div>
            <div class="match-vs-area">
              <div v-if="m.status==='pending'" class="match-time-text">{{ store.formatMatchTime(m.match_date) }}</div>
              <div v-else class="match-score-display">{{ m.scores_home }} - {{ m.scores_away }}</div>
              <div v-if="m.status==='live' && m.match_minute" style="font-size:13px;color:var(--accent);font-weight:700;">{{ m.match_minute }}'</div>
              <div v-else-if="m.status==='live'" style="font-size:10px;color:var(--red);">进行中</div>
            </div>
            <div class="match-team-col">
              <img v-if="m.away_logo_id" :src="`${logoBase}/${m.away_logo_id}.png`" class="team-logo" />
              <div v-else class="team-logo-fallback">{{ m.away_team.charAt(0) }}</div>
              <div class="match-team-name">{{ m.away_team }}</div>
            </div>
          </div>
          <div v-if="m.status==='pending'">
            <div v-if="m.has_odds" style="font-size:11px;color:var(--green-text);text-align:center;padding:4px 0;font-weight:600;">点击查看赔率下注</div>
            <div v-else style="font-size:11px;color:var(--text-muted);text-align:center;padding:4px 0;">赔率数据等待中</div>
          </div>
          <div v-if="m.status==='live'" style="font-size:11px;text-align:center;padding:4px 0;">
            <span v-if="m.has_odds" style="color:var(--accent);font-weight:600;">⚡ 滚球进行中 — 点击下注</span>
            <span v-else style="color:var(--text-muted);">赔率同步中...</span>
          </div>
        </div>
      </div>
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()

// Logo URL: 通过 Vercel rewrite 代理到服务器（避免 Mixed Content）
const logoBase = computed(() => '/team-logos')

const leagues = [
  { slug: 'international-world-cup', label: '🌍 世界杯', disabled: false, highlight: true },
  { slug: 'england-premier-league', label: '英超', disabled: false },
  { slug: 'spain-laliga', label: '西甲', disabled: false },
  { slug: 'germany-bundesliga', label: '德甲', disabled: false },
  { slug: 'italy-serie-a', label: '意甲', disabled: false },
  { slug: 'france-ligue-1', label: '法甲', disabled: false },
  { slug: 'international-clubs-uefa-champions-league', label: '🏆 欧冠决赛', disabled: false, highlight: true },
]

const selectedLeagues = ref([])
const activeTab = ref('all')
const tabs = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '即将开始' },
  { key: 'live', label: '进行中' },
  { key: 'settled', label: '已结束' },
]

function toggleLeague(slug) {
  if (leagues.find(l => l.slug === slug)?.disabled) return
  const idx = selectedLeagues.value.indexOf(slug)
  if (idx >= 0) {
    selectedLeagues.value.splice(idx, 1)
  } else {
    selectedLeagues.value.push(slug)
  }
  fetchData()
}

async function switchTab(key) {
  activeTab.value = key
  await fetchData()
}

async function fetchData() {
  const extra = {}
  if (selectedLeagues.value.length > 0) {
    extra.leagues = selectedLeagues.value.join(',')
  }
  await store.fetchMatches(activeTab.value, extra)
}

onMounted(async () => {
  await fetchData()
})
</script>
