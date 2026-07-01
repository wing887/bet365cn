import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useAppStore = defineStore('app', () => {
  const isLoggedIn = ref(false)
  const isAdminLoggedIn = ref(false)
  const isSuperAdmin = ref(false)
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)

  const matches = ref([])
  const myBets = ref([])
  const transactions = ref([])

  // ===== Auth =====
  async function restoreSession() {
    const t = localStorage.getItem('token')
    const u = localStorage.getItem('user')
    const a = localStorage.getItem('admin_user')
    if (t && u) { token.value = t; user.value = JSON.parse(u); isLoggedIn.value = true }
    if (t && a) { token.value = t; user.value = JSON.parse(a); isAdminLoggedIn.value = true; isSuperAdmin.value = JSON.parse(a).role === 'super_admin' }
  }

  async function loginUser(username, password) {
    const { data } = await api.post('/api/login', { username, password })
    token.value = data.token; user.value = data.user; isLoggedIn.value = true
    localStorage.setItem('token', data.token); localStorage.setItem('user', JSON.stringify(data.user))
  }

  async function loginAdmin(username, password) {
    const { data } = await api.post('/api/admin/login', { username, password })
    token.value = data.token; user.value = data.admin; isAdminLoggedIn.value = true
    isSuperAdmin.value = data.admin.role === 'super_admin'
    localStorage.setItem('token', data.token); localStorage.setItem('admin_user', JSON.stringify(data.admin))
  }

  function logout() {
    token.value = null; user.value = null; isLoggedIn.value = false; isAdminLoggedIn.value = false
    localStorage.clear()
  }

  async function fetchProfile() {
    const { data } = await api.get('/api/profile')
    user.value = data
  }

  // ===== Matches =====
  async function fetchHomeData() {
    const { data } = await api.get('/api/home')
    return data
  }

  async function fetchMatches(status, params = {}) {
    loading.value = true
    try {
      const p = { ...params }
      if (status !== 'all') p.status = status
      const { data } = await api.get('/api/matches', { params: p })
      matches.value = data.matches || []
      return data
    } finally { loading.value = false }
  }

  async function fetchMatchDetail(matchId) {
    const { data } = await api.get(`/api/matches/${matchId}`)
    return data
  }

  async function fetchMatchOdds(matchId) {
    const { data } = await api.get(`/api/matches/${matchId}/live-odds`)
    return data
  }

  // ===== Betting =====
  async function placeBet(matchId, marketType, selection, betAmount) {
    const { data } = await api.post('/api/bets', {
      match_id: matchId, market_type: marketType, selection, bet_amount: betAmount
    })
    if (user.value) user.value.coin_balance -= betAmount
    return data
  }

  async function fetchMyBets() {
    const { data } = await api.get('/api/bets')
    myBets.value = data.bets || []
    return data
  }

  async function fetchTransactions() {
    const { data } = await api.get('/api/coins/transactions')
    transactions.value = data.transactions || []
    return data
  }

  function getMatchStatusText(s) {
    const m = { pending:'即将开始', live:'进行中', settled:'已结束', cancelled:'已取消' }
    return m[s] || s
  }

  function getMarketName(mt) {
    const m = {
      ML:'独赢', Spread:'让球', Totals:'大/小', CS:'波胆',
      '1H_ML':'上半场独赢', '1H_Spread':'上半场让球', '1H_Totals':'上半场大/小',
      Kickoff:'开球', BTTS:'双方进球', OddEven:'单/双',
      Corner_Spread:'角球让球', Corner_Totals:'角球大小', Corner_ML:'角球独赢', Corner_OddEven:'角球单双',
      Cards_Spread:'罚牌让球', Cards_Totals:'罚牌大小', Cards_ML:'罚牌独赢', Cards_OddEven:'罚牌单双',
      TeamGoals:'球队进球', FirstLastGoal:'最先最后进球', HTFT:'半场全场', WinMargin:'净胜球', DoubleChance:'双重机会',
      PlayerGoals:'进球球员', Combo_ML_OU:'独赢&大小', Combo_ML_BTTS:'独赢&BTTS', Combo_OU_BTTS:'大小&BTTS',
    }
    return m[mt] || mt
  }

  function formatMatchTime(d) {
    if (!d) return ''
    const dt = new Date(d)
    return `${String(dt.getMonth()+1).padStart(2,'0')}/${String(dt.getDate()).padStart(2,'0')} ${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}`
  }

  return {
    isLoggedIn, isAdminLoggedIn, isSuperAdmin, user, token, loading,
    matches, myBets, transactions,
    restoreSession, loginUser, loginAdmin, logout, fetchProfile,
    fetchHomeData, fetchMatches, fetchMatchDetail, fetchMatchOdds,
    placeBet, fetchMyBets, fetchTransactions,
    getMatchStatusText, getMarketName, formatMatchTime,
  }
})
