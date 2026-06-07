<template>
  <div>
    <router-link to="/" class="back-link">← 返回</router-link>
    <div v-if="!match && store.loading" class="empty-state"><div class="empty-state-icon">⏳</div><div>加载中...</div></div>
    <template v-if="match">
      <!-- 比赛头部 -->
      <div class="card" style="margin-top:6px;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#0d1117;border-bottom:1px solid var(--border-light);font-size:10px;color:var(--text-muted);">
          <span>{{ match.league_name_cn || match.league_name }}</span>
          <span style="display:flex;align-items:center;gap:6px;">
            <span v-if="match.status==='live'" class="live-indicator-dot"></span>
            <span :class="'tag '+(match.status==='live'?'tag-red':match.status==='pending'?'tag-orange':'tag-green')">{{ store.getMatchStatusText(match.status) }}</span>
          </span>
        </div>
        <div style="padding:14px 12px;">
          <div class="match-teams-row">
            <div class="match-team-col">
              <img v-if="match.home_logo_id" :src="`/team-logos/${match.home_logo_id}.png`" class="team-logo-detail" />
              <div class="match-team-name">{{ match.home_team }}</div>
            </div>
            <div class="match-vs-area">
              <div v-if="match.status==='pending'" class="match-time-text">{{ store.formatMatchTime(match.match_date) }}</div>
              <div v-else class="match-score-display">{{ match.scores_home }} - {{ match.scores_away }}</div>
              <div v-if="match.status==='live' && match.match_minute" style="font-size:14px;color:var(--accent);font-weight:700;">{{ match.match_minute }}'</div>
              <div v-if="match.status==='live' && match.scores_p1_home !== undefined" style="font-size:10px;color:var(--text-muted);">半场 {{ match.scores_p1_home }}:{{ match.scores_p1_away }}</div>
            </div>
            <div class="match-team-col">
              <img v-if="match.away_logo_id" :src="`/team-logos/${match.away_logo_id}.png`" class="team-logo-detail" />
              <div class="match-team-name">{{ match.away_team }}</div>
            </div>
          </div>
          <!-- 实时刷新指示器 -->
          <div v-if="match.status==='live'" style="display:flex;align-items:center;justify-content:center;gap:4px;margin-top:6px;font-size:10px;color:var(--text-muted);">
            <span :class="pollingActive ? 'poll-dot-active' : 'poll-dot'"></span>
            {{ pollingActive ? '实时更新中' : '点击刷新' }}
            <button v-if="!pollingActive" class="btn-sm" @click="startPolling">开始实时</button>
          </div>
        </div>
      </div>

      <!-- 下注区域 -->
      <div v-if="(match.status==='pending' || match.status==='live') && (odds || liveOdds)" class="card">
        <div style="padding:12px;">
          <!-- 盘口标签 -->
          <div class="market-tabs" style="overflow-x:auto;flex-wrap:nowrap;gap:4px;">
            <button
              v-for="mt in marketTypes"
              :key="mt.key"
              class="market-tab"
              :class="{active:activeMarket===mt.key}"
              @click="activeMarket=mt.key;sel=''"
              style="white-space:nowrap;flex-shrink:0;"
            >{{ mt.label }}</button>
          </div>

          <!-- ML 胜平负 -->
          <div v-if="activeMarket==='ML'" class="bet-grid bet-grid-3">
            <div class="bet-option" :class="oddsFlashClass('home')" @click="quickSelect('home')">
              <span class="bet-option-label">主胜</span>
              <span class="bet-option-odds" :class="sel==='home'?'selected':''">{{ mlOdds.home }}</span>
            </div>
            <div class="bet-option" :class="oddsFlashClass('draw')" @click="quickSelect('draw')">
              <span class="bet-option-label">平局</span>
              <span class="bet-option-odds" :class="sel==='draw'?'selected':''">{{ mlOdds.draw }}</span>
            </div>
            <div class="bet-option" :class="oddsFlashClass('away')" @click="quickSelect('away')">
              <span class="bet-option-label">客胜</span>
              <span class="bet-option-odds" :class="sel==='away'?'selected':''">{{ mlOdds.away }}</span>
            </div>
          </div>

          <!-- Spread 让球盘 -->
          <div v-if="activeMarket==='Spread'" class="bet-grid">
            <div class="bet-option" :class="oddsFlashClass('Spread_home')" @click="quickSelect('home')">
              <span class="bet-option-label">主队赢盘</span>
              <span class="bet-option-hdp">{{ spreadHdp }}</span>
              <span class="bet-option-odds" :class="sel==='home'?'selected':''">{{ spreadOdds.home }}</span>
            </div>
            <div class="bet-option" :class="oddsFlashClass('Spread_away')" @click="quickSelect('away')">
              <span class="bet-option-label">客队赢盘</span>
              <span class="bet-option-hdp">{{ spreadHdp }}</span>
              <span class="bet-option-odds" :class="sel==='away'?'selected':''">{{ spreadOdds.away }}</span>
            </div>
          </div>

          <!-- Totals 大小球 -->
          <div v-if="activeMarket==='Totals'" class="bet-grid">
            <div class="bet-option" :class="oddsFlashClass('Totals_over')" @click="quickSelect('over')">
              <span class="bet-option-label">大 {{ totalsHdp }}</span>
              <span class="bet-option-odds" :class="sel==='over'?'selected':''">{{ totalsOdds.over }}</span>
            </div>
            <div class="bet-option" :class="oddsFlashClass('Totals_under')" @click="quickSelect('under')">
              <span class="bet-option-label">小 {{ totalsHdp }}</span>
              <span class="bet-option-odds" :class="sel==='under'?'selected':''">{{ totalsOdds.under }}</span>
            </div>
          </div>

          <!-- CS 波胆 -->
          <div v-if="activeMarket==='CS'" class="bet-grid">
            <div v-for="s in csScores" :key="s.label" class="bet-option" :class="{selected:sel===s.label}" @click="quickSelect(s.label)">
              <span class="bet-option-label">{{ s.label }}</span>
              <span class="bet-option-odds">@{{ s.odds }}</span>
            </div>
          </div>

          <!-- 封盘提示 -->
          <div v-if="isMarketSuspended" style="text-align:center;padding:20px;color:var(--red);font-size:13px;">
            ⛔ 该盘口暂时封盘
          </div>

          <!-- 下注操作区（未封盘） -->
          <div v-if="!isMarketSuspended">
            <div v-if="sel" style="margin-top:10px;">
              <div class="bet-limit-hint" style="text-align:center;font-size:12px;color:#999;margin-bottom:6px;">
                限额 {{ minBet }} ~ {{ limitMax }} 金币 <span v-if="isLive" style="color:var(--accent);">（滚球）</span>
              </div>
              <div class="bet-input-row">
                <input v-model.number="betAmount" type="number" class="input" :min="minBet" :max="limitMax" :placeholder="'金币（'+minBet+'-'+limitMax+'）'" />
                <button class="btn btn-accent btn-wide" :disabled="betting" @click="doBet">{{ betting?'下注中...':'确认下注' }}</button>
              </div>
              <div v-if="betAmount>=50&&currOdds>0" class="bet-summary" style="margin-top:10px;">
                <div class="bet-summary-text">预估奖励</div>
                <div class="bet-summary-amount">{{ Math.round(betAmount*currOdds) }} 金币</div>
                <div class="bet-summary-odds">赔率 @{{ currOdds }}</div>
              </div>
              <!-- 快速下注金额 -->
              <div v-if="isLive" style="display:flex;gap:6px;justify-content:center;margin-top:10px;">
                <button v-for="amt in quickAmounts" :key="amt" class="btn-sm quick-bet-btn" @click="betAmount=amt;doBet()">{{ amt }}</button>
              </div>
              <div v-if="betError" style="color:var(--red);font-size:12px;text-align:center;margin-top:6px;">{{ betError }}</div>
            </div>
            <div v-if="!sel" style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">
              {{ isLive ? '点击赔率快速下注' : '请选择投注选项' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 无赔率状态 -->
      <div v-if="(match.status==='pending' || match.status==='live') && !odds && !liveOdds" class="card">
        <div style="text-align:center;padding:20px;color:var(--text-muted);">赔率数据等待中...</div>
      </div>
      <div v-if="match.status==='settled'" class="card"><div style="text-align:center;padding:20px;color:var(--text-muted);">比赛已结束</div></div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../stores/app'
import api from '../api/client'

const store = useAppStore()
const route = useRoute()
const showToast = inject('showToast')

const activeMarket = ref('ML')
const sel = ref('')
const betAmount = ref(100)
const betting = ref(false)
const betError = ref('')
const betLimits = ref({ ml: 5000, spread: 5000, totals: 5000, cs: 1000 })
const liveBetLimits = ref({ ml: 3000, spread: 3000, totals: 3000, cs: 500 })

// 滚球实时数据
const liveOdds = ref(null)
const prevOdds = ref({})
const flashKeys = ref({})
const pollingActive = ref(false)
const pollTimer = ref(null)

const marketTypes = [
  {key:'ML',label:'胜平负'},
  {key:'Spread',label:'让球盘'},
  {key:'Totals',label:'大小球'},
  {key:'CS',label:'波胆'},
]

const quickAmounts = [100, 200, 500, 1000]

const match = computed(() => store.getMatchById(route.params.id))
const odds = computed(() => store.getOdds(route.params.id))
const isLive = computed(() => match.value?.status === 'live')

// 合并赔率：滚球优先
const currentOdds = computed(() => {
  if (isLive.value && liveOdds.value) return liveOdds.value
  return odds.value
})

const mlOdds = computed(() => {
  const d = currentOdds.value?.ML?.data
  return { home: d?.home || '-', draw: d?.draw || '-', away: d?.away || '-' }
})

const spreadHdp = computed(() => {
  const d = currentOdds.value?.Spread?.data
  if (!d) return ''
  const h = d.hdp
  return h > 0 ? `主队让${h}球` : h < 0 ? `主队受让${-h}球` : '平手盘'
})

const spreadOdds = computed(() => {
  const d = currentOdds.value?.Spread?.data
  return { home: d?.home || '-', away: d?.away || '-' }
})

const totalsHdp = computed(() => currentOdds.value?.Totals?.data?.hdp || '-')

const totalsOdds = computed(() => {
  const d = currentOdds.value?.Totals?.data
  return { over: d?.over || '-', under: d?.under || '-' }
})

const csScores = computed(() => currentOdds.value?.CS?.data?.scores || [])

const isMarketSuspended = computed(() => {
  if (!currentOdds.value) return true
  const mk = currentOdds.value[activeMarket.value]
  return mk?.status === 'suspended' || mk?.status === 'closed'
})

const currOdds = computed(() => {
  if (!currentOdds.value || !sel.value) return 0
  const o = currentOdds.value; const mk = activeMarket.value
  if (mk === 'ML') return o.ML?.data?.[sel.value] || 0
  if (mk === 'Spread') return o.Spread?.data?.[sel.value] || 0
  if (mk === 'Totals') return o.Totals?.data?.[sel.value] || 0
  if (mk === 'CS') { const s = csScores.value.find(x => x.label === sel.value); return s?.odds || 0 }
  return 0
})

const minBet = computed(() => 50)

const limitMax = computed(() => {
  const key = activeMarket.value.toLowerCase()
  if (isLive.value) return liveBetLimits.value[key] || 3000
  return betLimits.value[key] || 5000
})

function quickSelect(key) {
  if (isLive.value) {
    // 滚球模式：选择后直接弹出输入
    sel.value = key
    betAmount.value = 100
  } else {
    sel.value = key
  }
}

function oddsFlashClass(key) {
  if (flashKeys.value[key]) {
    const dir = flashKeys.value[key]
    return `odds-flash-${dir}`
  }
  return sel.value === key ? 'selected' : ''
}

// 检测赔率变化并触发闪烁动画
function detectOddsChange(newOdds) {
  if (!prevOdds.value) {
    prevOdds.value = newOdds
    return
  }
  const flash = {}
  const mkMap = { ML: ['home','draw','away'], Spread: ['home','away'], Totals: ['over','under'] }
  for (const [mk, keys] of Object.entries(mkMap)) {
    const oldD = prevOdds.value[mk]?.data || {}
    const newD = newOdds[mk]?.data || {}
    for (const k of keys) {
      const oldV = parseFloat(oldD[k]) || 0
      const newV = parseFloat(newD[k]) || 0
      if (oldV > 0 && newV > 0 && oldV !== newV) {
        flash[`${mk}_${k}`] = newV > oldV ? 'up' : 'down'
      }
    }
  }
  flashKeys.value = flash
  prevOdds.value = newOdds
  // 清除闪烁动画
  setTimeout(() => { flashKeys.value = {} }, 800)
}

// 滚球实时轮询
async function pollLiveOdds() {
  if (!isLive.value) return
  try {
    const r = await api.get(`/api/matches/${match.value.id}/live-odds`)
    if (r.data.odds) {
      detectOddsChange(r.data.odds)
      liveOdds.value = r.data.odds
    }
    // 更新比分和时间
    if (r.data.match_minute !== undefined) {
      store.matchDetail.match_minute = r.data.match_minute
      store.matchDetail.match_period = r.data.match_period
    }
    if (r.data.scores) {
      store.matchDetail.scores_home = r.data.scores.home
      store.matchDetail.scores_away = r.data.scores.away
      store.matchDetail.scores_p1_home = r.data.scores.p1_home
      store.matchDetail.scores_p1_away = r.data.scores.p1_away
    }
  } catch (e) {
    // silent fail on poll
  }
}

function startPolling() {
  pollingActive.value = true
  pollLiveOdds()
  pollTimer.value = setInterval(pollLiveOdds, 10000)
}

function stopPolling() {
  pollingActive.value = false
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

async function doBet() {
  if (!sel.value) return
  betting.value = true
  betError.value = ''
  try {
    const r = await store.placeBet(match.value.id, activeMarket.value, sel.value, betAmount.value)
    if (r.success) {
      showToast(`下注成功！预估 ${r.bet.potential_win} 金币`)
      sel.value = ''
      betAmount.value = 100
    }
  } catch (e) {
    betError.value = e.response?.data?.error || '下注失败'
  } finally {
    betting.value = false
  }
}

onMounted(async () => {
  await store.fetchMatchDetail(route.params.id)
  // 加载投注限额
  try {
    const r = await api.get('/api/bets/limits')
    if (r.data.limits) betLimits.value = r.data.limits
    if (r.data.live_limits) liveBetLimits.value = r.data.live_limits
  } catch (e) { /* use defaults */ }
  // 滚球比赛自动开始轮询
  if (match.value?.status === 'live') {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

// 监听路由变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    stopPolling()
    store.fetchMatchDetail(newId)
    liveOdds.value = null
    prevOdds.value = {}
    flashKeys.value = {}
  }
})
</script>

<style scoped>
.live-indicator-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #f44336;
  animation: livePulse 1.2s infinite;
}

@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.poll-dot-active {
  width: 6px; height: 6px; border-radius: 50%;
  background: #4caf50;
  animation: pollBlink 1s infinite;
}

.poll-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #666;
}

@keyframes pollBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.btn-sm {
  padding: 2px 8px; font-size: 11px; border: 1px solid var(--border);
  background: transparent; color: var(--text-muted); border-radius: 4px; cursor: pointer;
}

.quick-bet-btn {
  padding: 4px 10px; font-size: 12px;
  border: 1px solid var(--accent);
  background: transparent; color: var(--accent);
  border-radius: 4px; cursor: pointer;
  transition: background 0.15s;
}
.quick-bet-btn:active { background: var(--accent); color: #fff; }

.odds-flash-up {
  animation: flashGreen 0.6s ease;
}
.odds-flash-down {
  animation: flashRed 0.6s ease;
}

@keyframes flashGreen {
  0% { box-shadow: 0 0 8px rgba(76,175,80,0.6); border-color: #4caf50; }
  100% { box-shadow: none; border-color: var(--border); }
}

@keyframes flashRed {
  0% { box-shadow: 0 0 8px rgba(244,67,54,0.6); border-color: #f44336; }
  100% { box-shadow: none; border-color: var(--border); }
}
</style>
