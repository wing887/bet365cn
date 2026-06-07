<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">投注限额配置</div>
    <p class="page-desc">设置各盘口的赛前和滚球最大投注额。仅超级管理员可配置。</p>

    <div v-if="loading" class="empty-row">加载中...</div>

    <div v-else class="limits-grid">
      <div v-for="item in limits" :key="item.market_type" class="limit-card">
        <div class="limit-header">
          <span class="limit-icon">{{ marketIcons[item.market_type] || '📌' }}</span>
          <span class="limit-label">{{ item.label }}</span>
          <span class="limit-code">{{ item.market_type }}</span>
        </div>
        <div class="limit-body" style="margin-bottom:8px;">
          <label class="input-label">赛前限额</label>
          <input
            type="number"
            v-model.number="item.max_bet_amount"
            min="1"
            step="100"
            class="input limit-input"
          />
          <span class="limit-unit">金币</span>
        </div>
        <div class="limit-body">
          <label class="input-label" style="color:var(--accent);">滚球限额</label>
          <input
            type="number"
            v-model.number="item.live_max_bet_amount"
            min="1"
            step="100"
            class="input limit-input live-input"
          />
          <span class="limit-unit" style="color:var(--accent);">金币</span>
        </div>
        <div v-if="item.updated_at" class="limit-updated">
          上次更新：{{ formatTime(item.updated_at) }}
        </div>
      </div>
    </div>

    <div v-if="!loading" class="save-wrap">
      <button class="btn btn-primary" @click="save">保存设置</button>
      <span v-if="saved" class="save-ok">✅ 已保存</span>
      <span v-if="saveError" class="save-err">{{ saveError }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const showToast = inject('showToast')

const loading = ref(true)
const saved = ref(false)
const saveError = ref('')

const marketIcons = { ML: '⚽', Spread: '📊', Totals: '🔢', CS: '🎯' }

const limits = reactive([
  { market_type: 'ML', label: '胜平负', max_bet_amount: 5000, live_max_bet_amount: 3000, updated_at: null },
  { market_type: 'Spread', label: '让球盘', max_bet_amount: 5000, live_max_bet_amount: 3000, updated_at: null },
  { market_type: 'Totals', label: '大小球', max_bet_amount: 5000, live_max_bet_amount: 3000, updated_at: null },
  { market_type: 'CS', label: '波胆', max_bet_amount: 1000, live_max_bet_amount: 500, updated_at: null },
])

function formatTime(iso) {
  if (!iso) return '--'
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(async () => {
  try {
    const data = await store.fetchBetLimits()
    if (data.limits) {
      for (const key in data.limits) {
        const item = data.limits[key]
        const found = limits.find(l => l.market_type === item.market_type)
        if (found) {
          found.max_bet_amount = item.max_bet_amount
          found.live_max_bet_amount = item.live_max_bet_amount || Math.floor(item.max_bet_amount * 0.6)
          found.updated_at = item.updated_at
        }
      }
    }
  } catch (e) {
    showToast('加载限额失败', 'error')
  } finally {
    loading.value = false
  }
})

async function save() {
  saveError.value = ''
  saved.value = false
  const payload = {}
  for (const l of limits) {
    if (l.max_bet_amount < 1 || l.live_max_bet_amount < 1) {
      saveError.value = `${l.label} 金额不能小于1`
      return
    }
    payload[l.market_type.toLowerCase()] = l.max_bet_amount
    payload[`${l.market_type.toLowerCase()}_live`] = l.live_max_bet_amount
  }
  try {
    await store.updateBetLimits(payload)
    saved.value = true
    showToast('投注限额已更新', 'success')
    setTimeout(() => { saved.value = false }, 3000)
  } catch (e) {
    saveError.value = e?.response?.data?.error || '保存失败'
    showToast(saveError.value, 'error')
  }
}
</script>

<style scoped>
.page-desc {
  color: #999;
  font-size: 14px;
  margin-top: -8px;
  margin-bottom: 16px;
}
.limits-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.limit-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px;
}
.limit-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.limit-icon {
  font-size: 20px;
}
.limit-label {
  font-weight: 600;
  color: #e0e0e0;
}
.limit-code {
  margin-left: auto;
  font-size: 11px;
  color: #666;
  background: rgba(255,255,255,0.06);
  padding: 2px 6px;
  border-radius: 4px;
}
.limit-body {
  display: flex;
  align-items: center;
  gap: 6px;
}
.input-label {
  font-size: 11px;
  color: #888;
  min-width: 55px;
}
.limit-input {
  width: 90px;
  text-align: center;
  font-size: 18px;
  font-weight: 700;
}
.live-input {
  border-color: rgba(99,102,241,0.3);
}
.limit-unit {
  color: #999;
  font-size: 13px;
}
.limit-updated {
  margin-top: 8px;
  font-size: 11px;
  color: #555;
}
.save-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}
.save-ok {
  color: #4caf50;
  font-size: 14px;
}
.save-err {
  color: #f44336;
  font-size: 14px;
}
</style>
