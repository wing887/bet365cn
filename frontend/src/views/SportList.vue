<template>
  <div>
    <!-- League Header -->
    <div class="score_board">
      <div style="display:flex;align-items:center;gap:8px;" @click="router.back()">
        <span style="cursor:pointer;">← 返回</span>
      </div>
      <div class="score_league">{{ sportName }} · {{ periodName }}</div>
    </div>

    <!-- Market Filter Tabs -->
    <div class="filter_bar" style="border-bottom:1px solid var(--border-light);">
      <button v-for="t in filterTabs" :key="t.key" class="btn_filter" :class="{ on: activeFilter === t.key }" @click="activeFilter = t.key">{{ t.label }}</button>
    </div>

    <!-- Sub Filters -->
    <div class="filter_bar" style="background:#f8f8f8;" v-if="subFilters.length">
      <button v-for="s in subFilters" :key="s.key" class="btn_filter" :class="{ on: activeSubFilter === s.key }" @click="activeSubFilter = s.key">{{ s.label }}</button>
    </div>

    <div v-if="loading" class="page_loading">加载中...</div>

    <!-- Match List -->
    <div v-for="match in matches" :key="match.id" class="match_card" @click="openMatch(match.id)">
      <div class="match_card_top">
        <span>{{ match.league_name_cn || match.league_name }}</span>
        <span>
          <span v-if="match.status==='live'" style="color:var(--red);font-weight:700;">● 滚球</span>
          <span v-else>{{ formatTime(match.match_date) }}</span>
        </span>
      </div>
      <div class="match_card_body">
        <div class="match_teams">
          <span>{{ match.home_team }}</span>
          <span class="match_vs">V</span>
          <span>{{ match.away_team }}</span>
        </div>
        <div v-if="match.status==='live'" style="text-align:center;margin:4px 0;">
          <span class="match_score">{{ match.scores_home }} - {{ match.scores_away }}</span>
          <span v-if="match.match_minute" style="font-size:12px;color:var(--red);"> {{ match.match_minute }}'</span>
        </div>
        <!-- Quick odds preview (ML) -->
        <div v-if="match.odds && match.odds.ML" style="display:flex;gap:4px;margin-top:6px;">
          <div class="btn_odds" style="flex:1;font-size:11px;">
            <span style="display:block;font-size:9px;color:#999;">主</span>
            {{ match.odds.ML.data.home || '-' }}
          </div>
          <div class="btn_odds" style="flex:1;font-size:11px;">
            <span style="display:block;font-size:9px;color:#999;">和</span>
            {{ match.odds.ML.data.draw || '-' }}
          </div>
          <div class="btn_odds" style="flex:1;font-size:11px;">
            <span style="display:block;font-size:9px;color:#999;">客</span>
            {{ match.odds.ML.data.away || '-' }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && !matches.length" class="no_data">暂无赛事</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const loading = ref(true)
const matches = ref([])
const activeFilter = ref('main')
const activeSubFilter = ref('all')

const sport = ref(route.params.sport)
const period = ref(route.params.period)

const sportNames = { FT:'足球', BK:'篮球', TN:'网球' }
const periodNames = { live:'滚球', today:'今日', early:'早盘' }
const sportName = sportNames[sport.value] || sport.value
const periodName = periodNames[period.value] || period.value

const filterTabs = [
  { key: 'main', label: '主要玩法' },
  { key: 'spread', label: '让球&大小' },
  { key: 'cs', label: '波胆' },
  { key: 'combo', label: '独赢&大小' },
]
const subFilters = [
  { key: 'all', label: '全部' },
  { key: 'pre', label: '赛前' },
  { key: 'live', label: '滚球' },
]

function formatTime(d) {
  if (!d) return ''
  const dt = new Date(d)
  return `${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}`
}

function openMatch(id) { router.push(`/match/${id}`) }

onMounted(async () => {
  try {
    const status = period.value === 'live' ? 'live' : period.value === 'today' ? 'all' : 'pending'
    const data = await store.fetchMatches(status)
    matches.value = data.matches || []
  } catch(e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>
