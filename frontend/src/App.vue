<template>
  <div class="app-root">
    <!-- Header -->
    <header class="app-header">
      <div class="box_header">
        <div class="btn_home" :class="{ on: isHome }" @click="goHome">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
          </svg>
        </div>
        <div class="box_scroll header_scroll">
          <div class="box_slide dragscroll_header">
            <label>
              <div class="btn_header" :class="{ on: activeTab === 'live' }" @click="switchTab('live')">滚球</div>
              <div class="btn_header btn_special" :class="{ on: activeTab === 'wc' }" @click="switchTab('wc')">2026世界杯</div>
              <div class="btn_header btn_hot" :class="{ on: activeTab === 'hot' }" @click="switchTab('hot')">
                <i class="icon_fire"><svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M12 23c-4.4 0-8-3.6-8-8 0-3.6 3.2-8.2 6.8-13 .6-.8 1.8-.8 2.4 0 3.6 4.8 6.8 9.4 6.8 13 0 4.4-3.6 8-8 8z"/></svg></i>热门
              </div>
              <div class="btn_header" :class="{ on: activeTab === 'today' }" @click="switchTab('today')">今日</div>
              <div class="btn_header" :class="{ on: activeTab === 'soon' }" @click="switchTab('soon')">即将开赛</div>
              <div class="btn_header" :class="{ on: activeTab === 'early' }" @click="switchTab('early')">早盘</div>
              <div class="btn_header" :class="{ on: activeTab === 'outrights' }" @click="switchTab('outrights')">冠军</div>
              <div class="btn_header" :class="{ on: activeTab === 'parlay' }" @click="switchTab('parlay')">综合过关</div>
            </label>
          </div>
        </div>
        <div class="nav_header">
          <div class="money_header" v-if="store.isLoggedIn">
            <span class="text_money">
              <tt class="text_currency">RMB</tt>
              <tt class="text_credit">{{ store.user?.coin_balance || 0 }}</tt>
            </span>
            <div class="btn_acc" @click="toggleAccount">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v1.2c0 1 .8 1.8 1.8 1.8h15.6c1 0 1.8-.8 1.8-1.8v-1.2c0-3.2-6.4-4.8-9.6-4.8z"/></svg>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="content_l">
      <div class="box_l" ref="scrollBox">
        <router-view />
        <FooterSection />
      </div>
    </div>

    <!-- Bottom Nav -->
    <nav class="menu_bottom" v-if="showBottomNav">
      <div class="btn_nav" @click="router.push('/')">
        <i class="icon_tv"><svg viewBox="0 0 24 24" width="20" height="20"><rect x="2" y="3" width="20" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 21h8" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" stroke-width="1.5"/></svg></i>
        <span>电视直播</span>
      </div>
      <div class="btn_nav btn_myGame" @click="router.push('/my-events')">
        <i class="icon_star"><svg viewBox="0 0 16 16" width="20" height="20"><path fill="currentColor" d="M14.9,6.9l-2.4,2.9c-0.2,0.2-0.3,0.5-0.2,0.8l0.3,3.8c0,0.2-0.1,0.5-0.3,0.6c-0.2,0.1-0.4,0.1-0.6,0.1l-3.3-1.5c-0.3-0.1-0.5-0.1-0.8,0L4.3,15c-0.2,0.1-0.4,0.1-0.6-0.1c-0.2-0.1-0.3-0.4-0.3-0.6l0.3-3.8c0-0.3-0.1-0.5-0.2-0.8L1.1,6.9C0.9,6.7,0.9,6.5,1,6.3C1.1,6,1.2,5.9,1.4,5.8L5,5c0.3-0.1,0.5-0.2,0.6-0.5l1.9-3.3c0.2-0.4,0.8-0.4,1,0l1.9,3.3C10.5,4.8,10.7,4.9,11,5l3.6,0.8c0.2,0,0.4,0.2,0.4,0.4C15.1,6.5,15.1,6.7,14.9,6.9z"/></svg></i>
        <span>我的赛事</span>
      </div>
      <div class="btn_betslip" :class="{ betslip_exist: betslipCount > 0 }" @click="toggleBetslip">
        <i class="bet_amount">{{ betslipCount }}</i>
        <span class="text_betslip">
          <span class="betslip_name">注单</span>
        </span>
      </div>
      <div class="btn_nav btn_wager" @click="router.push('/my-bets')">
        <i class="num_betslip">{{ activeBetsCount }}</i>
        <span>投注记录</span>
      </div>
      <div class="btn_nav btn_myCredit" @click="toggleAccount" v-if="store.isLoggedIn">
        <i><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v1.2c0 1 .8 1.8 1.8 1.8h15.6c1 0 1.8-.8 1.8-1.8v-1.2c0-3.2-6.4-4.8-9.6-4.8z"/></svg></i>
        <span class="text_credit">{{ store.user?.coin_balance || 0 }}</span>
      </div>
    </nav>

    <!-- Bet Slip (bottom popup) -->
    <div class="bet_slip" :class="{ on: showBetslip }">
      <div class="ord_full_mask" @click="showBetslip = false"></div>
      <div class="ord_down_style" v-if="showBetslip">
        <div class="ord_title">
          <div class="ord_info">
            <span class="title_txt"><span>注单</span><code id="betCount">{{ betslipCount }}</code></span>
            <div class="balance cur">{{ store.user?.coin_balance || 0 }}</div>
            <button class="btn_remove_all" v-if="betslipCount > 0" @click="clearBetslip">移除全部</button>
          </div>
        </div>
        <div class="ord_content" v-if="betslipCount === 0">
          <div class="ord_empty">您的投注单为空。</div>
        </div>
        <div class="ord_content" v-else>
          <div class="bet_item" v-for="(item, idx) in betslipItems" :key="idx">
            <div class="bet_match">{{ item.home }} vs {{ item.away }}</div>
            <div class="bet_market">{{ item.marketName }} {{ item.selectionLabel }}</div>
            <div class="bet_odds">@{{ item.odds }}</div>
            <button class="btn_remove_one" @click="removeBetslipItem(idx)">×</button>
          </div>
          <div class="ord_bottom">
            <div class="ord_row"><span>下注总额</span><span>{{ totalStake }}</span></div>
            <div class="ord_row"><span>预估可赢</span><span>{{ estimatedWin }}</span></div>
            <input class="input_stake" type="number" v-model="stakeAmount" placeholder="金额" />
            <button class="btn_place" @click="placeBetslip">下注</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Account Slide (right) -->
    <div class="slide_r" :class="{ on: showAccount }" v-if="store.isLoggedIn">
      <div class="slide_mask" @click="showAccount = false"></div>
      <div class="slide_content">
        <div class="acc_user">
          <div class="acc_name">{{ store.user?.nickname || store.user?.username }}</div>
          <div class="acc_balance">RMB {{ store.user?.coin_balance || 0 }}</div>
        </div>
        <div class="acc_menu">
          <div class="acc_item" @click="router.push('/my-bets')">帐户历史</div>
          <div class="acc_item">设定</div>
          <div class="acc_item">帐户安全</div>
          <div class="acc_item" @click="store.logout(); router.push('/login')">退出登录</div>
        </div>
        <div class="acc_settings">
          <div class="acc_setting_row"><span>语言</span><span>简体 ▼</span></div>
          <div class="acc_setting_row"><span>盘口类型</span><span>香港盘 ▼</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from './stores/app'
import FooterSection from './components/FooterSection.vue'

const store = useAppStore()
const route = useRoute()
const router = useRouter()

const activeTab = ref('today')
const showBetslip = ref(false)
const showAccount = ref(false)
const betslipItems = ref([])
const stakeAmount = ref(0)

const isHome = computed(() => route.path === '/')
const showBottomNav = computed(() => !route.path.startsWith('/admin') && route.path !== '/login' && route.path !== '/dabiaoge')
const betslipCount = computed(() => betslipItems.value.length)
const activeBetsCount = ref(0)

const totalStake = computed(() => betslipItems.value.reduce((s, i) => s + i.amount, 0))
const estimatedWin = computed(() => {
  let mult = 1
  betslipItems.value.forEach(i => mult *= i.odds)
  return Math.round(stakeAmount.value * mult * 100) / 100
})

function switchTab(tab) { activeTab.value = tab; router.push('/') }
function goHome() { router.push('/') }
function toggleBetslip() { showBetslip.value = !showBetslip.value }
function toggleAccount() { showAccount.value = !showAccount.value }
function clearBetslip() { betslipItems.value = [] }

function addToBetslip(item) {
  const exists = betslipItems.value.find(i => i.matchId === item.matchId && i.market === item.market && i.selection === item.selection)
  if (exists) return
  betslipItems.value.push(item)
}

function removeBetslipItem(idx) { betslipItems.value.splice(idx, 1) }

async function placeBetslip() {
  if (stakeAmount.value <= 0) return alert('请输入下注金额')
  for (const item of betslipItems.value) {
    try {
      await store.placeBet(item.matchId, item.market, item.selection, stakeAmount.value)
    } catch(e) {
      alert(e.response?.data?.error || '下注失败')
      return
    }
  }
  alert('下注成功!')
  betslipItems.value = []
  stakeAmount.value = 0
  showBetslip.value = false
}

provide('addToBetslip', addToBetslip)
provide('store', store)

onMounted(async () => {
  await store.restoreSession()
  if (store.isLoggedIn) {
    store.fetchProfile().catch(() => {})
  }
})
</script>
