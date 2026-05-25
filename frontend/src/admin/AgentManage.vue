<template>
  <div class="admin-page">
    <div class="admin-header">
      <div>
        <router-link to="/admin" class="back-link">← 返回管理后台</router-link>
        <div class="page-title">代理管理</div>
        <div class="admin-info">查看代理经营数据及流水统计</div>
      </div>
    </div>

    <!-- 时间段选择 -->
    <div class="period-bar">
      <label>统计时段：</label>
      <input type="date" v-model="periodStart" class="date-input" />
      <span class="date-sep">至</span>
      <input type="date" v-model="periodEnd" class="date-input" />
      <button class="btn btn-primary btn-sm" @click="fetchAgents" style="margin-left:8px">查询</button>
      <span v-if="periodInfo" class="period-hint">{{ periodInfo }}</span>
    </div>

    <!-- 搜索 -->
    <div class="search-bar">
      <input v-model="searchQuery" placeholder="搜索代理用户名..." class="input" @input="onSearch" />
    </div>

    <!-- 代理列表 -->
    <div v-if="loading" class="loading-text">加载中...</div>

    <div v-else-if="agents.length === 0" class="empty-text">
      {{ searchQuery ? '未找到匹配的代理' : '暂无代理账号' }}
    </div>

    <div v-else class="agent-list">
      <div v-for="a in agents" :key="a.id" class="card" style="cursor:pointer" @click="selectAgent(a)">
        <div class="agent-row">
          <div class="agent-info">
            <div class="agent-name">
              {{ a.username }}
              <span class="tag tag-purple">代理</span>
              <span v-if="a.status === 'disabled'" class="tag tag-red">已封禁</span>
            </div>
            <div class="agent-meta">
              余额: <strong>{{ a.coin_balance || 0 }}</strong> 金币
              · 下游用户: <strong>{{ a.user_count }}</strong> 人
              · 近7天活跃: <strong>{{ a.active_users_7d }}</strong> 人
              · 本期流水: <strong>{{ a.turnover.toLocaleString() }}</strong> 金币
            </div>
          </div>
          <span class="arrow">›</span>
        </div>
      </div>
    </div>

    <!-- 代理详情弹窗 -->
    <div v-if="selectedAgent" class="modal-overlay" @click.self="closeDetail">
      <div class="modal-content modal-wide">
        <div class="modal-header">
          <h3>{{ selectedAgent.username }} - 经营详情</h3>
          <button class="btn-close" @click="closeDetail">✕</button>
        </div>

        <!-- 详情时间段 -->
        <div class="period-bar" style="margin-bottom:12px">
          <label>时段：</label>
          <input type="date" v-model="detailPeriodStart" class="date-input" />
          <span class="date-sep">至</span>
          <input type="date" v-model="detailPeriodEnd" class="date-input" />
          <button class="btn btn-primary btn-sm" @click="fetchDetail" style="margin-left:8px">查询</button>
        </div>

        <div v-if="detailLoading" class="loading-text">加载中...</div>

        <div v-else-if="detailData">
          <!-- 汇总卡片 -->
          <div class="summary-grid" style="margin-bottom:16px">
            <div class="summary-card">
              <div class="summary-value">{{ detailData.summary.total_users }}</div>
              <div class="summary-label">下游用户数</div>
            </div>
            <div class="summary-card">
              <div class="summary-value">{{ detailData.summary.active_users }}</div>
              <div class="summary-label">活跃用户</div>
            </div>
            <div class="summary-card">
              <div class="summary-value">{{ detailData.summary.total_turnover?.toLocaleString() }}</div>
              <div class="summary-label">总流水</div>
            </div>
            <div class="summary-card">
              <div class="summary-value" :class="{ 'text-green': detailData.summary.total_net > 0, 'text-red': detailData.summary.total_net < 0 }">
                {{ detailData.summary.total_net?.toLocaleString() }}
              </div>
              <div class="summary-label">净输赢</div>
            </div>
          </div>

          <!-- 用户列表 -->
          <div class="section-title">下游用户</div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>用户</th>
                  <th>余额</th>
                  <th>注数</th>
                  <th>流水</th>
                  <th>中奖</th>
                  <th>走水</th>
                  <th>净输赢</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in detailData.users" :key="u.id">
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
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const agents = ref([])
const loading = ref(false)
const searchQuery = ref('')
const periodStart = ref('')
const periodEnd = ref('')
const periodInfo = ref('')
let searchTimer = null

// 详情
const selectedAgent = ref(null)
const detailData = ref(null)
const detailLoading = ref(false)
const detailPeriodStart = ref('')
const detailPeriodEnd = ref('')

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
  fetchAgents()
})

async function fetchAgents() {
  loading.value = true
  try {
    const params = {}
    if (periodStart.value) params.period_start = periodStart.value
    if (periodEnd.value) params.period_end = periodEnd.value
    if (searchQuery.value) params.q = searchQuery.value

    const res = await api.get('/api/admin/agents', { params })
    agents.value = res.data.agents || []
    periodInfo.value = `统计时段: ${res.data.period_start} ~ ${res.data.period_end}`
  } catch (e) {
    console.error('获取代理列表失败', e)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchAgents, 300)
}

function selectAgent(agent) {
  selectedAgent.value = agent
  detailData.value = null
  detailPeriodStart.value = periodStart.value
  detailPeriodEnd.value = periodEnd.value
  fetchDetail()
}

function closeDetail() {
  selectedAgent.value = null
  detailData.value = null
}

async function fetchDetail() {
  if (!selectedAgent.value) return
  detailLoading.value = true
  try {
    const params = {}
    if (detailPeriodStart.value) params.period_start = detailPeriodStart.value
    if (detailPeriodEnd.value) params.period_end = detailPeriodEnd.value

    const res = await api.get(`/api/admin/agents/${selectedAgent.value.id}`, { params })
    detailData.value = res.data
  } catch (e) {
    console.error('获取代理详情失败', e)
  } finally {
    detailLoading.value = false
  }
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

.search-bar { margin-bottom: 16px; }
.search-bar .input { max-width: 300px; }

.loading-text { text-align: center; padding: 40px; color: #6b7280; }
.empty-text { text-align: center; padding: 40px; color: #6b7280; }

.agent-list { display: flex; flex-direction: column; gap: 8px; }

.agent-row {
  display: flex; align-items: center; justify-content: space-between;
}
.agent-info { flex: 1; }
.agent-name { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.agent-meta { font-size: 13px; color: #9ca3af; margin-top: 4px; }
.arrow { font-size: 20px; color: #6b7280; }

.tag-purple { background: #7c3aed20; color: #a78bfa; }
.tag-red { background: #ef444420; color: #f87171; }
.tag-sm { font-size: 11px; padding: 1px 6px; }

.user-name { font-weight: 500; }
.user-account { font-size: 12px; color: #6b7280; margin-left: 6px; }

.text-green { color: #34d399; }
.text-red { color: #f87171; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-content {
  background: #111827; border: 1px solid #1f2937; border-radius: 12px;
  padding: 24px; max-height: 85vh; overflow-y: auto;
}
.modal-wide { width: min(95vw, 900px); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.modal-header h3 { margin: 0; font-size: 18px; }
.btn-close { background: none; border: none; color: #9ca3af; font-size: 20px; cursor: pointer; }

/* Table */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 8px 10px; border-bottom: 1px solid #1f2937; color: #9ca3af; font-weight: 500; }
td { padding: 10px 10px; border-bottom: 1px solid #0f0f0f; }
</style>
