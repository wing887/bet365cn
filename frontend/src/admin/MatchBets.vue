<template>
  <div class="admin-page">
    <div class="admin-header">
      <div>
        <router-link to="/admin" class="back-link">← 返回管理后台</router-link>
        <div class="page-title">下注核对</div>
        <div class="admin-info">搜索用户，按比赛查看下注明细</div>
      </div>
    </div>

    <!-- 搜索用户 -->
    <div class="search-area">
      <div class="search-box">
        <input
          ref="searchInput"
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="输入用户名或昵称搜索..."
          @input="onSearchInput"
          @focus="onSearchFocus"
        />
        <span v-if="searchingUsers" class="search-spinner">⏳</span>
      </div>
      <div v-if="userCandidates.length > 0 && showCandidates" class="search-dropdown">
        <div
          v-for="u in userCandidates"
          :key="u.id"
          class="search-item"
          @click="selectUser(u)"
        >
          <span class="search-item-name">{{ u.nickname }}</span>
          <span class="search-item-account">({{ u.username }})</span>
          <span class="search-item-balance">🪙 {{ u.coin_balance }}</span>
        </div>
      </div>
    </div>

    <!-- 已选中用户 -->
    <div v-if="selectedUser" class="selected-user">
      <span class="selected-label">👤 {{ selectedUser.nickname }} ({{ selectedUser.username }})</span>
      <span class="selected-balance">余额: {{ selectedUser.coin_balance?.toLocaleString() }} 金币</span>
      <button class="btn-close-user" @click="clearUser">✕</button>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <label>时段：</label>
      <input type="date" v-model="periodStart" class="date-input" />
      <span class="date-sep">至</span>
      <input type="date" v-model="periodEnd" class="date-input" />
      <select v-model="statusFilter" class="filter-select">
        <option value="">全部状态</option>
        <option value="won">已赢</option>
        <option value="lost">已输</option>
        <option value="push">走水</option>
        <option value="pending">待结算</option>
      </select>
      <select v-model="marketFilter" class="filter-select">
        <option value="">全部盘口</option>
        <option value="ML">胜平负</option>
        <option value="Spread">让球盘</option>
        <option value="Totals">大小球</option>
        <option value="CS">波胆</option>
      </select>
      <button class="btn btn-primary btn-sm" @click="fetchBets" :disabled="!selectedUser">查询</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

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
          <div class="summary-value text-green">{{ data.summary.won_amount?.toLocaleString() }}</div>
          <div class="summary-label">中奖金额</div>
        </div>
        <div class="summary-card">
          <div class="summary-value text-red">{{ data.summary.lost_amount?.toLocaleString() }}</div>
          <div class="summary-label">输掉金额</div>
        </div>
        <div class="summary-card">
          <div class="summary-value text-gray">{{ data.summary.push_amount?.toLocaleString() }}</div>
          <div class="summary-label">走水退款</div>
        </div>
      </div>

      <!-- 比赛列表 -->
      <div v-if="data.matches.length === 0" class="empty-text">该时间段内无下注记录</div>

      <div v-else class="section-title">比赛明细（{{ data.matches.length }} 场）</div>

      <div v-for="m in data.matches" :key="m.match_id" class="match-group">
        <div class="match-header" @click="m.expanded = !m.expanded">
          <div class="match-info">
            <div class="match-teams">
              {{ m.home_team }} {{ m.scores_home }}:{{ m.scores_away }} {{ m.away_team }}
              <span v-if="m.status === 'live'" class="tag tag-live">滚球</span>
            </div>
            <div class="match-meta">
              {{ m.league_name }} · {{ formatDate(m.match_date) }}
            </div>
          </div>
          <div class="match-summary">
            <span>{{ m.bet_count }}注</span>
            <span class="match-summary-amount">{{ m.total_amount?.toLocaleString() }}金</span>
            <span :class="m.net_result >= 0 ? 'text-green' : 'text-red'">
              {{ m.net_result >= 0 ? '+' : '' }}{{ m.net_result?.toLocaleString() }}
            </span>
          </div>
          <span class="match-toggle">{{ m.expanded ? '▾' : '▸' }}</span>
        </div>

        <div v-if="m.expanded" class="match-bets">
          <div v-for="b in m.bets" :key="b.id" class="bet-row">
            <span class="bet-market">{{ getMarketLabel(b.market_type) }}</span>
            <span class="bet-sep">·</span>
            <span class="bet-selection">{{ getSelectionLabel(b.market_type, b.selection) }}</span>
            <span class="bet-odds">@{{ b.odds_value }}</span>
            <span class="bet-amount">投{{ b.bet_amount }}</span>
            <span class="bet-arrow">→</span>
            <span :class="statusClass(b)">
              {{ resultText(b) }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- 未搜索/未选中用户时的提示 -->
    <div v-if="!selectedUser && !loading" class="empty-text hint-text">
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

let searchTimer = null

function getDefaultDates() {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  return {
    start: firstDay.toISOString().slice(0, 10),
    end: now.toISOString().slice(0, 10),
  }
}

onMounted(() => {
  const d = getDefaultDates()
  periodStart.value = d.start
  periodEnd.value = d.end
})

function onSearchFocus() {
  if (searchQuery.value.trim() && userCandidates.value.length > 0) {
    showCandidates.value = true
  }
}

function onSearchInput() {
  clearTimeout(searchTimer)
  showCandidates.value = false

  const q = searchQuery.value.trim()
  if (q.length < 1) {
    userCandidates.value = []
    return
  }

  searchTimer = setTimeout(async () => {
    searchingUsers.value = true
    try {
      const res = await api.get('/api/admin/users', { params: { q, limit: 5 } })
      userCandidates.value = res.data.users || []
      if (userCandidates.value.length > 0) {
        showCandidates.value = true
      }
    } catch (e) {
      console.error('搜索用户失败', e)
    } finally {
      searchingUsers.value = false
    }
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
  } catch (e) {
    console.error('获取下注明细失败', e)
  } finally {
    loading.value = false
  }
}

function formatDate(d) {
  if (!d) return ''
  const dt = new Date(d)
  return `${(dt.getMonth() + 1).toString().padStart(2, '0')}/${dt.getDate().toString().padStart(2, '0')} ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`
}

function getMarketLabel(type) {
  const map = { ML: '胜平负', Spread: '让球', Totals: '大小', CS: '波胆' }
  return map[type] || type
}

function getSelectionLabel(marketType, selection) {
  if (marketType === 'ML') return { home: '主胜', draw: '平局', away: '客胜' }[selection] || selection
  if (marketType === 'Spread') return selection === 'home' ? '主队' : '客队'
  if (marketType === 'Totals') return selection === 'over' ? '大' : '小'
  return selection
}

function statusClass(b) {
  if (b.status === 'won') return 'text-green'
  if (b.status === 'lost') return 'text-red'
  if (b.status === 'push') return 'text-yellow'
  return 'text-gray'
}

function resultText(b) {
  if (b.status === 'won') return `+${b.win_amount}`
  if (b.status === 'lost') return `-${b.bet_amount}`
  if (b.status === 'push') return `退${b.bet_amount}`
  return '待定'
}
</script>

<style scoped>
.back-link {
  display: inline-block;
  color: #a78bfa; text-decoration: none; font-size: 13px;
  margin-bottom: 4px;
}
.back-link:hover { color: #c4b5fd; }

/* Search */
.search-area {
  position: relative; margin-bottom: 12px;
}
.search-box {
  display: flex; align-items: center;
}
.search-input {
  flex: 1; padding: 10px 14px;
  background: #1f2937; border: 1px solid #374151;
  color: #e5e7eb; border-radius: 8px; font-size: 14px;
  outline: none;
}
.search-input:focus { border-color: #a78bfa; }
.search-spinner { margin-left: -28px; font-size: 14px; }

.search-dropdown {
  position: absolute; top: 100%; left: 0; right: 0;
  background: #1f2937; border: 1px solid #374151;
  border-radius: 8px; margin-top: 4px; z-index: 50;
  max-height: 240px; overflow-y: auto;
}
.search-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; cursor: pointer;
  border-bottom: 1px solid #111827;
}
.search-item:last-child { border-bottom: none; }
.search-item:hover { background: #374151; }
.search-item-name { font-weight: 500; }
.search-item-account { font-size: 12px; color: #6b7280; }
.search-item-balance { font-size: 12px; color: #fbbf24; margin-left: auto; }

/* Selected user */
.selected-user {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; margin-bottom: 12px;
  background: #1a1035; border: 1px solid #7c3aed33;
  border-radius: 8px;
}
.selected-label { font-size: 15px; font-weight: 600; }
.selected-balance { font-size: 13px; color: #fbbf24; }
.btn-close-user {
  margin-left: auto; background: none; border: none;
  color: #6b7280; font-size: 16px; cursor: pointer;
}
.btn-close-user:hover { color: #f87171; }

/* Filters */
.filter-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; flex-wrap: wrap;
  font-size: 13px; color: #9ca3af;
}
.date-input {
  background: #1f2937; border: 1px solid #374151; color: #e5e7eb;
  padding: 5px 8px; border-radius: 6px; font-size: 13px;
}
.date-sep { color: #6b7280; }
.filter-select {
  background: #1f2937; border: 1px solid #374151;
  color: #e5e7eb; padding: 5px 8px;
  border-radius: 6px; font-size: 13px;
}

.loading-text { text-align: center; padding: 40px; color: #6b7280; }
.empty-text { text-align: center; padding: 40px; color: #6b7280; }
.hint-text { font-size: 14px; color: #6b7280; }

.text-green { color: #34d399; }
.text-red { color: #f87171; }
.text-yellow { color: #fbbf24; }
.text-gray { color: #9ca3af; }

.tag-live {
  background: #ef444420; color: #f87171;
  font-size: 11px; padding: 1px 6px; border-radius: 4px; margin-left: 6px;
}

/* Match groups */
.match-group {
  margin-bottom: 8px; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden;
}
.match-header {
  display: flex; align-items: center; padding: 10px 14px;
  background: #0f172a; cursor: pointer;
}
.match-info { flex: 1; }
.match-teams { font-weight: 600; font-size: 14px; }
.match-meta { font-size: 12px; color: #6b7280; margin-top: 2px; }
.match-summary {
  display: flex; gap: 12px; font-size: 13px; color: #9ca3af;
  margin-right: 8px; align-items: center;
}
.match-summary-amount { color: #d1d5db; }
.match-toggle { font-size: 16px; color: #6b7280; min-width: 20px; text-align: right; }

.match-bets { padding: 8px 14px; }
.bet-row {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 0; border-bottom: 1px solid #0f0f0f;
  font-size: 13px; flex-wrap: wrap;
}
.bet-row:last-child { border-bottom: none; }
.bet-market { color: #a78bfa; }
.bet-sep { color: #374151; }
.bet-selection { font-weight: 500; }
.bet-odds { color: #9ca3af; }
.bet-amount { color: #d1d5db; }
.bet-arrow { color: #6b7280; }
</style>
