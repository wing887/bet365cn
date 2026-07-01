<template>
  <div v-if="match">
    <!-- Score Board -->
    <div class="score_board">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;" @click="router.back()">
        <span style="cursor:pointer;">← 返回</span>
        <span style="font-size:12px;opacity:0.8;">{{ match.league_name_cn || match.league_name }}</span>
      </div>
      <div style="text-align:center;">
        <div class="score_time">
          <span v-if="match.status==='live'" style="color:var(--red);">● 滚球 {{ match.match_minute }}'</span>
          <span v-else>{{ formatTime(match.match_date) }}</span>
        </div>
      </div>
      <div class="score_teams">
        <div class="score_team">{{ match.home_team }}</div>
        <div class="score_box" v-if="match.status==='live'">
          <div class="score_num">{{ match.scores_home }} - {{ match.scores_away }}</div>
        </div>
        <div v-else class="match_vs" style="font-size:18px;color:var(--gold);">VS</div>
        <div class="score_team">{{ match.away_team }}</div>
      </div>
    </div>

    <!-- Market Filter Tabs -->
    <div class="filter_bar">
      <button v-for="t in marketTabs" :key="t.key" class="btn_filter" :class="{ on: activeTab === t.key }" @click="activeTab = t.key">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="page_loading">加载中...</div>

    <!-- Main Markets -->
    <div v-if="activeTab === 'main'">
      <div class="odds_list">
        <template v-for="mt in mainMarkets" :key="mt.key">
          <div class="title_game" style="font-size:12px;">
            <span style="color:var(--brown);font-weight:700;">{{ mt.label }}</span>
          </div>
          <div class="odds_item" v-if="match.odds && match.odds[mt.key]">
            <div style="flex:1;">
              <div v-if="mt.key === 'ML'">
                <div style="display:flex;gap:4px;">
                  <div class="btn_odds" :class="{ selected: selection === 'home' }" @click="addSlip('ML', 'home', match.odds.ML.data.home)">主 {{ match.odds.ML.data.home || '-' }}</div>
                  <div class="btn_odds" :class="{ selected: selection === 'draw' }" @click="addSlip('ML', 'draw', match.odds.ML.data.draw)">和 {{ match.odds.ML.data.draw || '-' }}</div>
                  <div class="btn_odds" :class="{ selected: selection === 'away' }" @click="addSlip('ML', 'away', match.odds.ML.data.away)">客 {{ match.odds.ML.data.away || '-' }}</div>
                </div>
              </div>
              <div v-else-if="['Spread','Totals','1H_Spread','1H_Totals'].includes(mt.key)">
                <div class="odds_item_inner" v-for="(line, idx) in (match.odds[mt.key].data.lines || [match.odds[mt.key].data])" :key="idx" style="display:flex;gap:4px;padding:4px 0;">
                  <div class="btn_odds" @click="addSlip(mt.key, mt.key.startsWith('1H')?'1h_'+line.sideA:(line.sideA||'home'), line.oddsA, line.hdp||'')">{{ line.labelA || '主' }} {{ line.hdp || '' }} <strong>{{ line.oddsA || '-' }}</strong></div>
                  <div class="btn_odds" @click="addSlip(mt.key, mt.key.startsWith('1H')?'1h_'+line.sideB:(line.sideB||'away'), line.oddsB, line.hdp||'')">{{ line.labelB || '客' }} {{ line.hdp || '' }} <strong>{{ line.oddsB || '-' }}</strong></div>
                </div>
              </div>
              <div v-else-if="mt.key === 'BTTS'">
                <div style="display:flex;gap:4px;">
                  <div class="btn_odds" @click="addSlip('BTTS','yes',match.odds.BTTS.data.yes)">是 {{ match.odds.BTTS.data.yes || '-' }}</div>
                  <div class="btn_odds" @click="addSlip('BTTS','no',match.odds.BTTS.data.no)">否 {{ match.odds.BTTS.data.no || '-' }}</div>
                </div>
              </div>
              <div v-else-if="mt.key === 'Kickoff'">
                <div style="display:flex;gap:4px;">
                  <div class="btn_odds" @click="addSlip('Kickoff','home',match.odds.Kickoff.data.home)">主队 {{ match.odds.Kickoff.data.home || '-' }}</div>
                  <div class="btn_odds" @click="addSlip('Kickoff','away',match.odds.Kickoff.data.away)">客队 {{ match.odds.Kickoff.data.away || '-' }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="odds_item" v-else>
            <div style="color:#999;text-align:center;width:100%;padding:12px;">暂无赔率</div>
          </div>
        </template>
      </div>
    </div>

    <!-- Other Tabs (暂无) -->
    <div v-else class="odds_list">
      <div class="title_game"><span>{{ tabLabel }}</span></div>
      <div class="odds_item"><div style="color:#999;text-align:center;width:100%;padding:24px;">暂无赔率数据</div></div>
    </div>
  </div>
  <div v-else class="page_loading">加载中...</div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()
const addToBetslip = inject('addToBetslip', () => {})

const match = ref(null)
const loading = ref(true)
const activeTab = ref('main')
const selection = ref('')

const marketTabs = [
  { key: 'main', label: '主要玩法' },
  { key: 'spread', label: '让球&大小' },
  { key: 'corner', label: '角球' },
  { key: 'cards', label: '罚牌数' },
  { key: 'cs', label: '波胆' },
  { key: 'player', label: '进球球员' },
  { key: 'combo', label: '独赢&大小' },
]

const tabLabel = computed(() => {
  return marketTabs.find(t => t.key === activeTab.value)?.label || ''
})

const mainMarkets = [
  { key: 'Spread', label: '让球' },
  { key: 'Totals', label: '大/小' },
  { key: 'ML', label: '独赢' },
  { key: '1H_Spread', label: '上半场 让球' },
  { key: '1H_Totals', label: '上半场 大/小' },
  { key: '1H_ML', label: '上半场 独赢' },
  { key: 'Kickoff', label: '开球' },
  { key: 'BTTS', label: '双方球队进球' },
]

function formatTime(d) {
  if (!d) return ''
  return store.formatMatchTime(d)
}

function addSlip(market, sel, odds, hdp = '') {
  selection.value = sel
  const marketName = store.getMarketName(market)
  addToBetslip({
    matchId: match.value.id,
    home: match.value.home_team,
    away: match.value.away_team,
    market,
    marketName,
    selection: sel,
    selectionLabel: sel === 'home' ? '主胜' : sel === 'away' ? '客胜' : sel === 'draw' ? '和局' : sel === 'over' ? '大' : sel === 'under' ? '小' : sel === 'yes' ? '是' : sel === 'no' ? '否' : sel,
    odds,
    amount: 100,
  })
}

onMounted(async () => {
  try {
    match.value = await store.fetchMatchOdds(route.params.id)
  } catch(e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>
