<template>
  <div>
    <router-link to="/" class="back-link">← 返回</router-link>

    <div class="card" v-if="match" style="margin-top:6px;">
      <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#FAFAFA;border-bottom:1px solid var(--border-light);font-size:10px;color:var(--text-muted);">
        <span>{{ match.league_name }}</span>
        <span :class="'tag ' + (match.status === 'live' ? 'tag-red' : match.status === 'pending' ? 'tag-orange' : 'tag-green')">{{ store.getMatchStatusText(match.status) }}</span>
      </div>
      <div style="padding:14px 12px;">
        <div class="match-teams-row">
          <div class="match-team-col"><div class="match-team-name">{{ match.home_team }}</div></div>
          <div class="match-vs-area">
            <div v-if="match.status === 'pending'" class="match-time-text">{{ store.formatMatchTime(match.match_date) }}</div>
            <div v-else class="match-score-display">{{ match.scores_home }} - {{ match.scores_away }}</div>
          </div>
          <div class="match-team-col"><div class="match-team-name">{{ match.away_team }}</div></div>
        </div>
      </div>
    </div>

    <!-- Pending: betting -->
    <div v-if="match && match.status === 'pending' && odds" class="card">
      <div style="padding:12px;">
        <div class="market-tabs">
          <button v-for="mt in marketTypes" :key="mt.key" class="market-tab" :class="{ active: activeMarket === mt.key }" @click="activeMarket = mt.key; selectedOption = ''">{{ mt.label }}</button>
        </div>

        <div v-if="activeMarket === 'ML'" class="bet-grid bet-grid-3">
          <div class="bet-option" :class="{ selected: selectedOption === 'home' }" @click="selectedOption = 'home'">
            <span class="bet-option-label">主胜</span>
            <span class="bet-option-odds">{{ odds.ML.home }}</span>
          </div>
          <div class="bet-option" :class="{ selected: selectedOption === 'draw' }" @click="selectedOption = 'draw'">
            <span class="bet-option-label">平局</span>
            <span class="bet-option-odds">{{ odds.ML.draw }}</span>
          </div>
          <div class="bet-option" :class="{ selected: selectedOption === 'away' }" @click="selectedOption = 'away'">
            <span class="bet-option-label">客胜</span>
            <span class="bet-option-odds">{{ odds.ML.away }}</span>
          </div>
        </div>

        <div v-if="activeMarket === 'Spread'" class="bet-grid">
          <div class="bet-option" :class="{ selected: selectedOption === 'home' }" @click="selectedOption = 'home'">
            <span class="bet-option-hdp">{{ spreadHomeLabel }}</span>
            <span class="bet-option-label">主队赢盘</span>
            <span class="bet-option-odds">{{ odds.Spread.home }}</span>
          </div>
          <div class="bet-option" :class="{ selected: selectedOption === 'away' }" @click="selectedOption = 'away'">
            <span class="bet-option-hdp">{{ spreadAwayLabel }}</span>
            <span class="bet-option-label">客队赢盘</span>
            <span class="bet-option-odds">{{ odds.Spread.away }}</span>
          </div>
        </div>

        <div v-if="activeMarket === 'Totals'" class="bet-grid">
          <div class="bet-option" :class="{ selected: selectedOption === 'over' }" @click="selectedOption = 'over'">
            <span class="bet-option-label">大 {{ odds.Totals.hdp }}</span>
            <span class="bet-option-odds">{{ odds.Totals.over }}</span>
          </div>
          <div class="bet-option" :class="{ selected: selectedOption === 'under' }" @click="selectedOption = 'under'">
            <span class="bet-option-label">小 {{ odds.Totals.hdp }}</span>
            <span class="bet-option-odds">{{ odds.Totals.under }}</span>
          </div>
        </div>

        <div v-if="activeMarket === 'CS'" class="bet-grid">
          <div v-for="s in odds.CS.scores" :key="s.label" class="bet-option" :class="{ selected: selectedOption === s.label }" @click="selectedOption = s.label">
            <span class="bet-option-label">{{ s.label }}</span>
            <span class="bet-option-odds">@{{ s.odds }}</span>
          </div>
        </div>

        <div v-if="selectedOption" style="margin-top:10px;">
          <div class="bet-input-row">
            <input v-model.number="betAmount" type="number" class="input" placeholder="金币数（最低50）" />
            <button class="btn btn-accent btn-wide" @click="doBet">确认下注</button>
          </div>
          <div v-if="betAmount >= 50 && currentOdds > 0" class="bet-summary" style="margin-top:10px;">
            <div class="bet-summary-text">预估奖励</div>
            <div class="bet-summary-amount">{{ Math.round(betAmount * currentOdds) }} 金币</div>
            <div class="bet-summary-odds">赔率 @{{ currentOdds }}</div>
          </div>
        </div>

        <div v-if="!selectedOption" style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">
          请选择投注选项
        </div>
      </div>
    </div>

    <div v-if="match && match.status === 'live'" class="card">
      <div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">
        比赛进行中，滚球下注将于 V2.0 开放
      </div>
    </div>
    <div v-if="match && match.status === 'settled'" class="card">
      <div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">
        比赛已结束
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../stores/mockData'
const store = useAppStore()
const route = useRoute()
const showToast = inject('showToast')
const activeMarket = ref('ML')
const selectedOption = ref('')
const betAmount = ref(100)
const marketTypes = [
  { key: 'ML', label: '胜平负' },
  { key: 'Spread', label: '让球盘' },
  { key: 'Totals', label: '大小球' },
  { key: 'CS', label: '波胆' },
]
const match = computed(() => store.getMatchById(route.params.id))
const odds = computed(() => store.getOdds(route.params.id))
const spreadHomeLabel = computed(() => {
  if (!odds.value) return ''
  const h = odds.value.Spread.hdp
  return h > 0 ? `主队让${h}球` : h < 0 ? `主队受让${-h}球` : '平手盘'
})
const spreadAwayLabel = computed(() => {
  if (!odds.value) return ''
  const h = odds.value.Spread.hdp
  return h > 0 ? `客队受让${h}球` : h < 0 ? `客队让${-h}球` : '平手盘'
})
const currentOdds = computed(() => {
  if (!odds.value || !selectedOption.value) return 0
  const o = odds.value
  if (activeMarket.value === 'ML') return o.ML[selectedOption.value] || 0
  if (activeMarket.value === 'Spread') return o.Spread[selectedOption.value] || 0
  if (activeMarket.value === 'Totals') return o.Totals[selectedOption.value] || 0
  if (activeMarket.value === 'CS') { const s = o.CS.scores.find(x => x.label === selectedOption.value); return s ? s.odds : 0 }
  return 0
})
function doBet() {
  if (!selectedOption.value) return
  const result = store.placeBet(match.value.id, activeMarket.value, selectedOption.value, betAmount.value)
  showToast(result.success ? `下注成功！预估 ${result.win} 金币` : result.msg, result.success ? 'success' : 'error')
  if (result.success) { selectedOption.value = ''; betAmount.value = 100 }
}
</script>
