<template>
  <div class="admin-page">
    <div class="admin-header">
      <div>
        <router-link to="/admin" class="back-link">← 返回管理后台</router-link>
        <div class="page-title">客户统计</div>
        <div class="admin-info">查看名下客户的投注流水与输赢详情</div>
      </div>
    </div>

    <!-- 时间段选择 -->
    <div class="period-bar">
      <label>统计时段：</label>
      <input type="date" v-model="periodStart" class="date-input" />
      <span class="date-sep">至</span>
      <input type="date" v-model="periodEnd" class="date-input" />
      <button class="btn btn-primary btn-sm" @click="fetchStats" style="margin-left:8px">查询</button>
      <span v-if="periodInfo" class="period-hint">{{ periodInfo }}</span>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

    <template v-else-if="data">
      <!-- 汇总卡片 -->
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.total_users }}</div>
          <div class="summary-label">客户总数</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.active_users }}</div>
          <div class="summary-label">活跃客户</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.total_bet_count }}</div>
          <div class="summary-label">总注数</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ data.summary.total_turnover?.toLocaleString() }}</div>
          <div class="summary-label">总流水</div>
        </div>
        <div class="summary-card">
          <div class="summary-value text-green">{{ data.summary.total_win?.toLocaleString() }}</div>
          <div class="summary-label">用户中奖</div>
        </div>
        <div class="summary-card">
          <div class="summary-value text-gray">{{ data.summary.total_push?.toLocaleString() }}</div>
          <div class="summary-label">走水退款</div>
        </div>
        <div class="summary-card">
          <div class="summary-value" :class="{ 'text-green': data.summary.total_net > 0, 'text-red': data.summary.total_net < 0 }">
            {{ data.summary.total_net?.toLocaleString() }}
          </div>
          <div class="summary-label">净输赢</div>
        </div>
      </div>

      <!-- 客户列表 -->
      <div v-if="data.users.length === 0" class="empty-text" style="padding:20px">该时间段内无投注记录</div>

      <div v-else class="section-title">客户明细</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>客户</th>
              <th>余额</th>
              <th>注数</th>
              <th>流水</th>
              <th>中奖</th>
              <th>走水</th>
              <th>净输赢</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in data.users" :key="u.id">
              <td>
                <span class="user-name">{{ u.nickname }}</span>
                <span class="user-account">({{ u.username }})</span>
                <span v-if="u.status === 'disabled'" class="tag tag-red tag-sm">已封禁</span>
              </td>
              <td>{{ u.coin_balance?.toLocaleString() }}</td>
              <td>{{ u.bet_count }}</td>
              <td>{{ u.turnover?.toLocaleString() }}</td>
              <td class="text-green">{{ u.win_amount?.toLocaleString() }}</td>
              <td>{{ u.push_refund?.toLocaleString() }}</td>
              <td :class="{ 'text-green': u.net > 0, 'text-red': u.net < 0 }">{{ u.net?.toLocaleString() }}</td>
              <td><button class="btn btn-outline btn-xs" @click="openDaily(u)">明细</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- 用户每日明细弹窗 -->
    <div v-if="dailyUser" class="modal-overlay" @click.self="closeDaily">
      <div class="modal-content modal-wide">
        <div class="modal-header">
          <h3>{{ dailyUser.nickname }} ({{ dailyUser.username }}) - 投注明细</h3>
          <button class="btn-close" @click="closeDaily">✕</button>
        </div>

        <!-- 时间段 -->
        <div class="period-bar" style="margin-bottom:12px">
          <label>时段：</label>
          <input type="date" v-model="dailyPeriodStart" class="date-input" />
          <span class="date-sep">至</span>
          <input type="date" v-model="dailyPeriodEnd" class="date-input" />
          <button class="btn btn-primary btn-sm" @click="fetchDaily" style="margin-left:8px">查询</button>
        </div>

        <div v-if="dailyLoading" class="loading-text">加载中...</div>

        <div v-else-if="dailyData">
          <!-- 汇总 -->
          <div class="summary-grid" style="margin-bottom:12px">
            <div class="summary-card">
              <div class="summary-value">{{ dailyData.summary.total_days }}</div>
              <div class="summary-label">天数</div>
            </div>
            <div class="summary-card">
              <div class="summary-value">{{ dailyData.summary.total_bets }}</div>
              <div class="summary-label">总注数</div>
            </div>
            <div class="summary-card">
              <div class="summary-value">{{ dailyData.summary.total_turnover?.toLocaleString() }}</div>
              <div class="summary-label">总流水</div>
            </div>
            <div class="summary-card">
              <div class="summary-value" :class="{ 'text-green': dailyData.summary.total_net > 0, 'text-red': dailyData.summary.total_net < 0 }">
                {{ dailyData.summary.total_net?.toLocaleString() }}
              </div>
              <div class="summary-label">净输赢</div>
            </div>
          </div>

          <!-- 按天分组 -->
          <div v-for="day in dailyData.daily" :key="day.date" class="day-group">
            <div class="day-header" @click="day.expanded = !day.expanded">
              <span class="day-date">{{ day.date }}</span>
              <span class="day-stats">
                {{ day.bet_count }}注 · 流水 {{ day.turnover?.toLocaleString() }}
                · <span :class="{ 'text-green': day.net > 0, 'text-red': day.net < 0 }">净{{ day.net >= 0 ? '+' : '' }}{{ day.net?.toLocaleString() }}</span>
              </span>
              <span class="day-toggle">{{ day.expanded ? '▾' : '▸' }}</span>
            </div>
            <div v-if="day.expanded" class="day-bets">
              <div v-for="b in day.bets" :key="b.id" class="bet-item">
                <div class="bet-left">
                  <span class="bet-match">{{ b.match_home }} vs {{ b.match_away }}</span>
                  <span class="bet-league">{{ b.league_name }}</span>
                </div>
                <div class="bet-right">
                  <span class="bet-detail">{{ getMarketName(b.market_type) }} · {{ getSelectionLabel(b.market_type, b.selection) }} · @{{ b.odds_value }}</span>
                  <span class="bet-amount">投{{ b.bet_amount }} → 
                    <span :class="{ 'text-green': b.status === 'won', 'text-red': b.status === 'lost', 'text-yellow': b.status === 'push' }">
                      {{ b.status === 'won' ? '+' + b.win_amount : b.status === 'push' ? '退' + b.bet_amount : '-' + b.bet_amount }}
                    </span>
                  </span>
                </div>
              </div>
              <div v-if="day.bets.length === 0" class="empty-text">无投注</div>
            </div>
          </div>

          <div v-if="dailyData.daily.length === 0" class="empty-text" style="padding:20px">该时间段内无投注记录</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const loading = ref(false)
const periodStart = ref('')
const periodEnd = ref('')
const periodInfo = ref('')
const data = ref(null)

// 每日明细
const dailyUser = ref(null)
const dailyData = ref(null)
const dailyLoading = ref(false)
const dailyPeriodStart = ref('')
const dailyPeriodEnd = ref('')

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
  fetchStats()
})

async function fetchStats() {
  loading.value = true
  try {
    const params = {}
    if (periodStart.value) params.period_start = periodStart.value
    if (periodEnd.value) params.period_end = periodEnd.value

    const res = await api.get('/api/agent/customers/stats', { params })
    data.value = res.data
    periodInfo.value = `统计时段: ${res.data.period_start} ~ ${res.data.period_end}`
  } catch (e) {
    console.error('获取客户统计失败', e)
  } finally {
    loading.value = false
  }
}

function openDaily(user) {
  dailyUser.value = user
  dailyData.value = null
  dailyPeriodStart.value = periodStart.value
  dailyPeriodEnd.value = periodEnd.value
  fetchDaily()
}

function closeDaily() {
  dailyUser.value = null
  dailyData.value = null
}

async function fetchDaily() {
  if (!dailyUser.value) return
  dailyLoading.value = true
  try {
    const params = {}
    if (dailyPeriodStart.value) params.period_start = dailyPeriodStart.value
    if (dailyPeriodEnd.value) params.period_end = dailyPeriodEnd.value

    const res = await api.get(`/api/agent/customers/${dailyUser.value.id}/daily`, { params })
    dailyData.value = res.data
  } catch (e) {
    console.error('获取客户明细失败', e)
  } finally {
    dailyLoading.value = false
  }
}

function getMarketName(type) {
  const map = { ML: '胜平负', Spread: '让球盘', Totals: '大小球', CS: '波胆' }
  return map[type] || type
}

function getSelectionLabel(marketType, selection) {
  if (marketType === 'ML') return { home: '主胜', draw: '平局', away: '客胜' }[selection] || selection
  if (marketType === 'Spread') return selection === 'home' ? '主队' : '客队'
  if (marketType === 'Totals') return selection === 'over' ? '大' : '小'
  return selection
}
</script>

<style scoped>
.back-link {
  display: inline-block;
  color: #a78bfa; text-decoration: none; font-size: 13px;
  margin-bottom: 4px;
}
.back-link:hover { color: #c4b5fd; }

.period-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px;
  font-size: 14px; color: #9ca3af;
}
.date-input {
  background: #1f2937; border: 1px solid #374151; color: #e5e7eb;
  padding: 4px 8px; border-radius: 6px; font-size: 13px;
}
.date-sep { color: #6b7280; }
.period-hint { font-size: 12px; color: #6b7280; margin-left: 12px; }

.loading-text { text-align: center; padding: 40px; color: #6b7280; }
.empty-text { text-align: center; padding: 40px; color: #6b7280; }

.tag-red { background: #ef444420; color: #f87171; }
.tag-sm { font-size: 11px; padding: 1px 6px; }

.user-name { font-weight: 500; }
.user-account { font-size: 12px; color: #6b7280; margin-left: 6px; }

.text-green { color: #34d399; }
.text-red { color: #f87171; }
.text-yellow { color: #fbbf24; }
.text-gray { color: #9ca3af; }

.btn-xs { font-size: 12px; padding: 2px 10px; }

/* Table */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 8px 10px; border-bottom: 1px solid #1f2937; color: #9ca3af; font-weight: 500; }
td { padding: 10px 10px; border-bottom: 1px solid #0f0f0f; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-content {
  background: #111827; border: 1px solid #1f2937; border-radius: 12px;
  padding: 24px; max-height: 85vh; overflow-y: auto;
}
.modal-wide { width: min(95vw, 880px); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.modal-header h3 { margin: 0; font-size: 18px; }
.btn-close { background: none; border: none; color: #9ca3af; font-size: 20px; cursor: pointer; }

/* Day groups */
.day-group { margin-bottom: 8px; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden; }
.day-header {
  display: flex; align-items: center; padding: 10px 14px;
  background: #0f172a; cursor: pointer;
  justify-content: space-between;
}
.day-date { font-weight: 600; font-size: 14px; }
.day-stats { font-size: 13px; color: #9ca3af; }
.day-toggle { font-size: 16px; color: #6b7280; min-width: 20px; text-align: right; }
.day-bets { padding: 8px 14px; }
.bet-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid #0f0f0f;
  font-size: 13px;
}
.bet-item:last-child { border-bottom: none; }
.bet-left { display: flex; flex-direction: column; }
.bet-match { font-weight: 500; }
.bet-league { font-size: 11px; color: #6b7280; }
.bet-right { display: flex; flex-direction: column; align-items: flex-end; }
.bet-detail { color: #9ca3af; font-size: 12px; }
.bet-amount { font-weight: 600; }
</style>
