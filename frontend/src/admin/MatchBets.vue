<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">下注核对</div>

    <!-- 搜索栏 -->
    <div class="card search-bar" style="position:relative">
      <input
        ref="searchInput"
        v-model="searchQuery"
        class="input"
        placeholder="输入用户名或昵称搜索..."
        @input="onSearchInput"
        @focus="onSearchFocus"
      />
      <span v-if="searchingUsers" style="margin-left:-24px;font-size:13px">⏳</span>
      <!-- 下拉候选 -->
      <div v-if="userCandidates.length > 0 && showCandidates" class="search-dropdown">
        <div
          v-for="u in userCandidates"
          :key="u.id"
          class="search-dropdown-item"
          @click="selectUser(u)"
        >
          <span>{{ u.nickname }} ({{ u.username }})</span>
          <span style="color:var(--b365-green);font-weight:600">🪙 {{ u.coin_balance }}</span>
        </div>
      </div>
    </div>

    <!-- 已选中用户 -->
    <div v-if="selectedUser" class="card form-card selected-user-card">
      <div class="form-row">
        <span style="font-weight:700;font-size:14px">👤 {{ selectedUser.nickname }}（{{ selectedUser.username }}）</span>
        <span style="color:var(--b365-green);font-weight:600;font-size:13px">余额：{{ selectedUser.coin_balance?.toLocaleString() }} 金币</span>
        <span class="tag" :class="selectedUser.status === 'active' ? 'tag-green' : 'tag-red'" style="margin-left:auto">
          {{ selectedUser.status === 'active' ? '活跃' : '封禁' }}
        </span>
        <button class="btn btn-sm" style="background:#f0f0f0;color:#999;margin-left:8px" @click="clearUser">✕</button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="card form-card">
      <div class="form-title">筛选条件</div>
      <div class="form-row">
        <input type="date" v-model="periodStart" class="input" />
        <span class="date-sep">至</span>
        <input type="date" v-model="periodEnd" class="input" />
        <select v-model="statusFilter" class="input" style="flex:0.8">
          <option value="">全部状态</option>
          <option value="won">已赢</option>
          <option value="lost">已输</option>
          <option value="push">走水</option>
          <option value="pending">待结算</option>
        </select>
        <select v-model="marketFilter" class="input" style="flex:0.8">
          <option value="">全部盘口</option>
          <option value="ML">胜平负</option>
          <option value="Spread">让球盘</option>
          <option value="Totals">大小球</option>
          <option value="CS">波胆</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="fetchBets" :disabled="!selectedUser">查询</button>
      </div>
      <div v-if="periodInfo" class="form-hint">{{ periodInfo }}</div>
    </div>

    <div v-if="loading" class="empty-row">加载中...</div>

    <template v-else-if="data">
      <!-- 汇总卡片 -->
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.total_bets }}</div>
          <div class="summary-label">总注数</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.total_matches }}</div>
          <div class="summary-label">比赛场次</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.total_amount?.toLocaleString() }}</div>
          <div class="summary-label">总流水</div>
        </div>
        <div class="summary-card">
          <div class="summary-value green">+{{ data.summary.won_amount?.toLocaleString() }}</div>
          <div class="summary-label">中奖金额</div>
        </div>
        <div class="summary-card">
          <div class="summary-value red">-{{ data.summary.lost_amount?.toLocaleString() }}</div>
          <div class="summary-label">输掉金额</div>
        </div>
        <div class="summary-card">
          <div class="summary-value" style="color:var(--text-muted)">{{ data.summary.push_amount?.toLocaleString() }}</div>
          <div class="summary-label">走水退款</div>
        </div>
      </div>

      <!-- 比赛列表 -->
      <div v-if="data.matches.length === 0" class="empty-row">该时间段内无下注记录</div>

      <template v-else>
        <div class="section-title">比赛明细（{{ data.matches.length }} 场）</div>
        <div class="card">
          <div v-for="m in data.matches" :key="m.match_id" class="match-block">
            <div class="match-header" @click="m.expanded = !m.expanded">
              <div class="match-header-left">
                <div class="match-teams">
                  {{ m.home_team }} {{ m.scores_home }}:{{ m.scores_away }} {{ m.away_team }}
                  <span v-if="m.status === 'live'" class="tag tag-red" style="margin-left:4px">滚球</span>
                  <span v-else-if="m.status === 'pending'" class="tag tag-orange">未开赛</span>
                </div>
                <div class="match-meta">{{ m.league_name }} · {{ formatDate(m.match_date) }}</div>
              </div>
              <div class="match-header-right">
                <span class="match-stats">{{ m.bet_count }}注 · {{ m.total_amount?.toLocaleString() }}金</span>
                <span :class="m.net_result >= 0 ? 'green' : 'red'" style="font-weight:700">
                  {{ m.net_result >= 0 ? '+' : '' }}{{ m.net_result?.toLocaleString() }}
                </span>
                <span class="match-arrow">{{ m.expanded ? '▾' : '▸' }}</span>
              </div>
            </div>
            <div v-if="m.expanded" class="match-bets">
              <div v-for="b in m.bets" :key="b.id" class="bet-row">
                <span class="bet-market">{{ getMarketLabel(b.market_type) }}</span>
                <span class="bet-selection">{{ getSelectionLabel(b.market_type, b.selection) }}</span>
                <span class="bet-odds">@{{ b.odds_value }}</span>
                <span class="bet-amount">投{{ b.bet_amount }}</span>
                <span class="bet-arrow">→</span>
                <span :class="resultClass(b)" class="bet-result">
                  {{ resultText(b) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- 初始提示 -->
    <div v-if="!selectedUser && !loading" class="empty-row" style="padding:40px 0;color:var(--text-muted);font-size:13px">
      🔍 上方搜索并选择用户，然后点击「查询」查看下注明细
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const searchQuery = ref('')
const searchInput = ref(null)
const userCandidates = ref([])
const showCandidates = ref(false)
const searchingUsers = ref(false)
const selectedUser = ref(null)

const periodStart = ref('')
const periodEnd = ref('')
const statusFilter = ref('')
const marketFilter = ref('')
const loading = ref(false)
const data = ref(null)
const periodInfo = ref('')

let searchTimer = null

function getDefaultDates() {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  return { start: firstDay.toISOString().slice(0, 10), end: now.toISOString().slice(0, 10) }
}

onMounted(() => {
  const d = getDefaultDates()
  periodStart.value = d.start
  periodEnd.value = d.end
})

function onSearchFocus() {
  if (searchQuery.value.trim() && userCandidates.value.length > 0) showCandidates.value = true
}

function onSearchInput() {
  clearTimeout(searchTimer)
  showCandidates.value = false
  const q = searchQuery.value.trim()
  if (q.length < 1) { userCandidates.value = []; return }
  searchTimer = setTimeout(async () => {
    searchingUsers.value = true
    try {
      const res = await api.get('/api/admin/users', { params: { q, limit: 5 } })
      userCandidates.value = res.data.users || []
      if (userCandidates.value.length > 0) showCandidates.value = true
    } catch (e) { /* ignore */ } finally { searchingUsers.value = false }
  }, 300)
}

function selectUser(user) {
  selectedUser.value = user
  searchQuery.value = user.nickname
  showCandidates.value = false
  userCandidates.value = []
  data.value = null
}

function clearUser() {
  selectedUser.value = null
  searchQuery.value = ''
  data.value = null
}

async function fetchBets() {
  if (!selectedUser.value) return
  loading.value = true
  try {
    const params = {}
    if (periodStart.value) params.period_start = periodStart.value
    if (periodEnd.value) params.period_end = periodEnd.value
    if (statusFilter.value) params.status = statusFilter.value
    if (marketFilter.value) params.market_type = marketFilter.value
    const res = await api.get(`/api/admin/users/${selectedUser.value.id}/match-bets`, { params })
    data.value = res.data
    periodInfo.value = `统计时段：${res.data.period_start} ~ ${res.data.period_end}`
  } catch (e) { console.error('获取下注明细失败', e) } finally { loading.value = false }
}

function formatDate(d) {
  if (!d) return ''
  const dt = new Date(d)
  return `${(dt.getMonth() + 1).toString().padStart(2, '0')}/${dt.getDate().toString().padStart(2, '0')} ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`
}

function getMarketLabel(type) {
  return { ML: '胜平负', Spread: '让球', Totals: '大小', CS: '波胆' }[type] || type
}

function getSelectionLabel(marketType, selection) {
  if (marketType === 'ML') return { home: '主胜', draw: '平局', away: '客胜' }[selection] || selection
  if (marketType === 'Spread') return selection === 'home' ? '主队' : '客队'
  if (marketType === 'Totals') return selection === 'over' ? '大' : '小'
  return selection
}

function resultClass(b) {
  if (b.status === 'won') return 'green'
  if (b.status === 'lost') return 'red'
  if (b.status === 'push') return ''
  return ''
}

function resultText(b) {
  if (b.status === 'won') return '+' + b.win_amount
  if (b.status === 'lost') return '-' + b.bet_amount
  if (b.status === 'push') return '退' + b.bet_amount
  return '待定'
}
</script>

<style scoped>
/* Search dropdown */
.search-dropdown {
  position: absolute; top: 100%; left: 0; right: 0;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); margin-top: 4px; z-index: 50;
  max-height: 240px; overflow-y: auto; box-shadow: var(--shadow-md);
}
.search-dropdown-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; cursor: pointer; font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}
.search-dropdown-item:last-child { border-bottom: none; }
.search-dropdown-item:hover { background: #F5F5F5; }

/* Selected user card */
.selected-user-card { padding: 12px !important; }

/* Match blocks */
.match-block {
  border-bottom: 1px solid var(--border-light);
}
.match-block:last-child { border-bottom: none; }

.match-header {
  display: flex; align-items: center; padding: 12px 14px;
  cursor: pointer; gap: 8px;
}
.match-header:hover { background: #FAFAFA; }

.match-header-left { flex: 1; min-width: 0; }
.match-teams { font-weight: 700; font-size: 14px; }
.match-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.match-header-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.match-stats { font-size: 12px; color: var(--text-secondary); }
.match-arrow { font-size: 14px; color: var(--text-muted); min-width: 16px; text-align: right; }

/* Bet rows */
.match-bets { padding: 0 14px 10px; }
.bet-row {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 0; font-size: 12px;
  border-bottom: 1px dotted var(--border-light);
}
.bet-row:last-child { border-bottom: none; }
.bet-market { color: var(--b365-green); font-weight: 600; }
.bet-selection { font-weight: 500; color: var(--text-primary); }
.bet-odds { color: var(--text-muted); }
.bet-amount { color: var(--text-secondary); }
.bet-arrow { color: var(--text-muted); }
.bet-result { font-weight: 700; margin-left: 2px; }
</style>
