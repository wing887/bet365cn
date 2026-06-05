<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">封盘管理</div>
    <p class="page-desc">查看和管理各场比赛的盘口状态。封盘后用户无法对该盘口下注。</p>

    <div v-if="loading" class="empty-row">加载中...</div>

    <div v-else>
      <!-- 筛选 -->
      <div class="filter-bar">
        <button
          v-for="f in filters"
          :key="f.key"
          class="filter-btn"
          :class="{ active: activeFilter === f.key }"
          @click="activeFilter = f.key"
        >{{ f.label }}</button>
      </div>

      <div v-if="filteredMatches.length === 0" class="empty-row">
        {{ activeFilter === 'pending' ? '暂无待开赛比赛' : '暂无进行中比赛' }}
      </div>

      <div v-for="m in filteredMatches" :key="m.id" class="match-card">
        <div class="match-header">
          <span class="match-league">{{ m.league_name_cn || m.league_name }}</span>
          <span class="match-time">{{ formatTime(m.match_date) }}</span>
          <span :class="'tag ' + (m.status === 'live' ? 'tag-red' : 'tag-orange')">
            {{ m.status === 'live' ? '进行中' : '待开赛' }}
          </span>
        </div>
        <div class="match-teams">
          {{ m.home_team }} <span class="vs">vs</span> {{ m.away_team }}
        </div>
        <div class="market-statuses">
          <div v-for="mk in (m.markets || [])" :key="mk.id" class="market-row">
            <span class="market-type">{{ mk.label }}</span>
            <span :class="'status-badge status-' + mk.status">
              {{ statusText(mk.status) }}
            </span>
            <div class="market-actions">
              <button
                v-if="mk.status !== 'active'"
                class="btn btn-xs btn-success"
                @click="toggleStatus(m.id, mk.market_type, 'active')"
                :disabled="toggling"
              >开盘</button>
              <button
                v-if="mk.status === 'active'"
                class="btn btn-xs btn-warning"
                @click="toggleStatus(m.id, mk.market_type, 'suspended')"
                :disabled="toggling"
              >封盘</button>
              <button
                v-if="mk.status !== 'closed'"
                class="btn btn-xs btn-danger"
                @click="toggleStatus(m.id, mk.market_type, 'closed')"
                :disabled="toggling"
              >关闭</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const showToast = inject('showToast')

const loading = ref(true)
const toggling = ref(false)
const activeFilter = ref('pending')
const matchesWithOdds = ref([])

const filters = [
  { key: 'pending', label: '待开赛' },
  { key: 'live', label: '进行中' },
]

const filteredMatches = computed(() => {
  return matchesWithOdds.value.filter(m => m.status === activeFilter.value)
})

function statusText(s) {
  const map = { active: '开盘', suspended: '封盘', closed: '已关闭' }
  return map[s] || s
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
}

async function loadData() {
  try {
    await store.fetchMatches('all')
    const matches = store.matches.filter(m => m.status === 'pending' || m.status === 'live')
    const result = []
    for (const m of matches) {
      try {
        const r = await store.fetchMarketStatus(m.id)
        if (r.markets && r.markets.length > 0) {
          result.push({ ...m, ...r.match, markets: r.markets })
        }
      } catch (e) { /* skip */ }
    }
    matchesWithOdds.value = result
  } catch (e) {
    showToast('加载失败', 'error')
  } finally {
    loading.value = false
  }
}

async function toggleStatus(matchId, marketType, newStatus) {
  toggling.value = true
  try {
    await store.updateMarketStatus(matchId, marketType, newStatus)
    showToast(`已${newStatus === 'active' ? '开盘' : newStatus === 'suspended' ? '封盘' : '关闭'}`, 'success')
    // 刷新本地状态
    const m = matchesWithOdds.value.find(x => x.id === matchId)
    if (m) {
      const mk = m.markets.find(x => x.market_type === marketType)
      if (mk) mk.status = newStatus
    }
  } catch (e) {
    showToast(e?.response?.data?.error || '操作失败', 'error')
  } finally {
    toggling.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-desc {
  color: #999;
  font-size: 14px;
  margin-top: -8px;
  margin-bottom: 16px;
}
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.filter-btn {
  padding: 6px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.12);
  background: transparent;
  color: #999;
  cursor: pointer;
  font-size: 13px;
}
.filter-btn.active {
  background: rgba(99,102,241,0.2);
  border-color: rgba(99,102,241,0.5);
  color: #818cf8;
}
.match-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
}
.match-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.match-league {
  font-size: 12px;
  color: #818cf8;
}
.match-time {
  font-size: 12px;
  color: #999;
}
.match-teams {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}
.vs {
  color: #666;
  margin: 0 8px;
}
.market-statuses {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.market-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  background: rgba(255,255,255,0.02);
  border-radius: 6px;
}
.market-type {
  width: 60px;
  font-size: 13px;
  color: #ccc;
}
.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}
.status-active { background: rgba(76,175,80,0.2); color: #4caf50; }
.status-suspended { background: rgba(255,152,0,0.2); color: #ff9800; }
.status-closed { background: rgba(244,67,54,0.2); color: #f44336; }
.market-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}
.btn-xs {
  padding: 3px 10px;
  font-size: 11px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}
.btn-success { background: #4caf50; color: white; }
.btn-warning { background: #ff9800; color: white; }
.btn-danger { background: #f44336; color: white; }
.btn-xs:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
