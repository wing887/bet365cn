<template>
  <div>
    <div class="score_board">
      <div style="display:flex;align-items:center;gap:8px;" @click="router.back()">
        <span style="cursor:pointer;">← 返回</span>
      </div>
      <div class="score_league">投注记录</div>
    </div>
    <div class="filter_bar">
      <button v-for="t in tabs" :key="t.key" class="btn_filter" :class="{ on: activeTab === t.key }" @click="activeTab = t.key">{{ t.label }}</button>
    </div>
    <div v-if="loading" class="page_loading">加载中...</div>
    <div v-else-if="filtered.length === 0" class="no_data">暂无投注记录</div>
    <div v-else class="match_card" v-for="b in filtered" :key="b.id" style="margin:4px 8px;">
      <div style="padding:10px;">
        <div style="font-weight:700;font-size:14px;">{{ b.match_home }} vs {{ b.match_away }}</div>
        <div style="font-size:12px;color:#999;">{{ b.league_name }} · {{ store.getMarketName(b.market_type) }} · {{ b.selection }}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
          <span style="font-size:12px;">{{ b.bet_amount }} @{{ b.odds_value }}</span>
          <span v-if="b.status==='won'" style="color:#2E7D32;font-weight:700;">+{{ b.win_amount }}</span>
          <span v-else-if="b.status==='lost'" style="color:var(--red);">-{{ b.bet_amount }}</span>
          <span v-else style="color:#E65100;">待结算</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const router = useRouter()
const store = useAppStore()
const loading = ref(true)
const activeTab = ref('all')
const tabs = [
  { key: 'all', label: '全部' }, { key: 'pending', label: '待结算' }, { key: 'won', label: '已赢' }, { key: 'lost', label: '已输' }
]

const filtered = computed(() => {
  if (activeTab.value === 'all') return store.myBets
  return store.myBets.filter(b => b.status === activeTab.value)
})

onMounted(async () => {
  await store.fetchMyBets()
  loading.value = false
})
</script>
