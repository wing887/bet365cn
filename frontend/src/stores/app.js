import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useAppStore = defineStore('app', () => {
  // ===== Auth =====
  const isLoggedIn = ref(false)
  const isAdminLoggedIn = ref(false)
  const isSuperAdmin = ref(false)
  const user = ref(null)
  const token = ref(null)

  // ===== Data =====
  const matches = ref([])
  const matchDetail = ref(null)
  const oddsCache = ref({})
  const myBets = ref([])
  const transactions = ref([])
  const loading = ref(false)

  // ===== Admin data =====
  const adminUsers = ref([])
  const adminAccounts = ref([])
  const pendingSettlements = ref([])
  const operationLogs = ref([])

  // ===== Helpers =====
  function getMatchStatusText(status) {
    const map = { pending: '即将开始', live: '进行中', settled: '已结束', cancelled: '已取消' }
    return map[status] || status
  }

  function getBetStatusText(status) {
    const map = { pending: '待结算', won: '已赢', lost: '已输', push: '走水', refunded: '已退款' }
    return map[status] || status
  }

  function getMarketName(type) {
    const map = { ML: '胜平负', Spread: '让球盘', Totals: '大小球', CS: '波胆' }
    return map[type] || type
  }

  function getSelectionLabel(marketType, selection) {
    if (marketType === 'ML') return { home: '主胜', draw: '平局', away: '客胜' }[selection] || selection
    if (marketType === 'Spread') return selection === 'home' ? '主队赢盘' : '客队赢盘'
    if (marketType === 'Totals') return selection === 'over' ? '大球' : '小球'
    return selection
  }

  function formatMatchTime(iso) {
    if (!iso) return '---'
    const d = new Date(iso)
    const now = new Date()
    const pad = n => String(n).padStart(2, '0')
    const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`
    if (d.toDateString() === now.toDateString()) return '今天 ' + time
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${time}`
  }

  function formatDate(iso) {
    if (!iso) return '---'
    return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
  }

  // ===== Auth Actions =====
  async function loginUser(username, password) {
    const res = await api.post('/api/auth/login', { username, password })
    token.value = res.data.token.access_token
    user.value = res.data.user
    isLoggedIn.value = true
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    return res.data
  }

  async function loginAdmin(username, password) {
    const res = await api.post('/api/admin/auth/login', { username, password })
    token.value = res.data.token.access_token
    user.value = res.data.admin
    isAdminLoggedIn.value = true
    isSuperAdmin.value = res.data.admin.is_super_admin
    localStorage.setItem('token', token.value)
    localStorage.setItem('admin_user', JSON.stringify(user.value))
    return res.data
  }

  async function restoreSession() {
    const t = localStorage.getItem('token')
    const u = localStorage.getItem('user')
    const a = localStorage.getItem('admin_user')
    if (t && a) {
      token.value = t
      user.value = JSON.parse(a)
      isAdminLoggedIn.value = true
      isSuperAdmin.value = user.value?.is_super_admin || false
      return true
    }
    if (t && u) {
      token.value = t
      user.value = JSON.parse(u)
      isLoggedIn.value = true
      return true
    }
    // Dev mode: auto login with test account for real API data
    if (import.meta.env.DEV) {
      try {
        const res = await api.post('/api/auth/login', { username: 'test', password: '123' })
        token.value = res.data.token.access_token
        user.value = res.data.user
        isLoggedIn.value = true
        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        return true
      } catch (e) {
        // Fallback to mock
        isLoggedIn.value = true
        user.value = { id: 1, username: 'test', nickname: '测试用户', coin_balance: 100000 }
        return true
      }
    }
    return false
  }

  function logout() {
    isLoggedIn.value = false
    isAdminLoggedIn.value = false
    isSuperAdmin.value = false
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('admin_user')
    matches.value = []
    myBets.value = []
    transactions.value = []
  }

  async function changePassword(oldPwd, newPwd) {
    const res = await api.post('/api/auth/change-password', { old_password: oldPwd, new_password: newPwd })
    return res.data
  }

  // ===== User Actions =====
  async function fetchMatches(status = 'all', extraParams = {}) {
    loading.value = true
    try {
      const params = { status, ...extraParams }
      const res = await api.get('/api/matches', { params })
      matches.value = res.data.matches || []
    } catch (e) {
      if (import.meta.env.DEV) {
        matches.value = getMockMatches()
      }
    } finally {
      loading.value = false
    }
  }

  function getMockMatches() {
    return [
      { id: 1, home_team: '曼城', away_team: '阿森纳', home_logo_id: '65', away_logo_id: '57', league_name_cn: '英超', league_name: 'England - Premier League', match_date: '2026-05-22T19:00:00Z', status: 'pending', scores_home: 0, scores_away: 0, has_odds: true },
      { id: 2, home_team: '拜仁慕尼黑', away_team: '多特蒙德', home_logo_id: '5', away_logo_id: '4', league_name_cn: '德甲', league_name: 'Germany - Bundesliga', match_date: '2026-05-22T19:30:00Z', status: 'live', scores_home: 1, scores_away: 0, has_odds: true },
      { id: 3, home_team: '皇家马德里', away_team: '巴塞罗那', home_logo_id: '86', away_logo_id: '81', league_name_cn: '西甲', league_name: 'Spain - LaLiga', match_date: '2026-05-22T18:00:00Z', status: 'settled', scores_home: 3, scores_away: 1, has_odds: true },
      { id: 4, home_team: '尤文图斯', away_team: '国际米兰', home_logo_id: '109', away_logo_id: '108', league_name_cn: '意甲', league_name: 'Italy - Serie A', match_date: '2026-05-22T20:00:00Z', status: 'pending', scores_home: 0, scores_away: 0, has_odds: true },
      { id: 5, home_team: '巴黎圣日耳曼', away_team: '里昂', home_logo_id: '524', away_logo_id: '523', league_name_cn: '法甲', league_name: 'France - Ligue 1', match_date: '2026-05-22T20:30:00Z', status: 'pending', scores_home: 0, scores_away: 0, has_odds: true },
      { id: 6, home_team: '利物浦', away_team: '切尔西', home_logo_id: '64', away_logo_id: '61', league_name_cn: '英超', league_name: 'England - Premier League', match_date: '2026-05-22T21:00:00Z', status: 'pending', scores_home: 0, scores_away: 0, has_odds: true },
      { id: 7, home_team: 'AC米兰', away_team: '那不勒斯', home_logo_id: '98', away_logo_id: '113', league_name_cn: '意甲', league_name: 'Italy - Serie A', match_date: '2026-05-22T18:30:00Z', status: 'settled', scores_home: 2, scores_away: 2, has_odds: true },
      { id: 8, home_team: '马德里竞技', away_team: '塞维利亚', home_logo_id: '78', away_logo_id: '559', league_name_cn: '西甲', league_name: 'Spain - LaLiga', match_date: '2026-05-22T19:00:00Z', status: 'live', scores_home: 0, scores_away: 1, has_odds: true },
      { id: 9, home_team: '莱斯特城', away_team: '南安普顿', home_logo_id: null, away_logo_id: '340', league_name_cn: '英超', league_name: 'England - Premier League', match_date: '2026-05-22T22:00:00Z', status: 'pending', scores_home: 0, scores_away: 0, has_odds: false },
      { id: 10, home_team: '蒙扎', away_team: '威尼斯', home_logo_id: null, away_logo_id: null, league_name_cn: '意甲', league_name: 'Italy - Serie A', match_date: '2026-05-22T22:00:00Z', status: 'pending', scores_home: 0, scores_away: 0, has_odds: false },
    ]
  }

  async function fetchMatchDetail(matchId) {
    const res = await api.get(`/api/matches/${matchId}`)
    matchDetail.value = res.data
    if (res.data.odds) oddsCache.value[matchId] = res.data.odds
    return res.data
  }

  function getMatchById(id) {
    return matches.value.find(m => m.id === Number(id)) || matchDetail.value
  }

  function getOdds(matchId) {
    return oddsCache.value[matchId] || null
  }

  async function placeBet(matchId, marketType, selection, betAmount) {
    const res = await api.post('/api/bets', { match_id: matchId, market_type: marketType, selection, bet_amount: betAmount })
    const data = res.data
    if (data.success && user.value) {
      user.value.coin_balance = data.balance
    }
    return data
  }

  async function fetchMyBets(status = 'all') {
    const res = await api.get('/api/bets', { params: { status } })
    myBets.value = res.data.bets || []
  }

  async function fetchTransactions(page = 1) {
    const res = await api.get('/api/transactions', { params: { page, per_page: 20 } })
    transactions.value = res.data.transactions || []
    return res.data
  }

  async function fetchProfile() {
    const res = await api.get('/api/profile')
    user.value = res.data
    return res.data
  }

  // ===== Admin Actions =====
  async function fetchAdminUsers() {
    const res = await api.get('/api/admin/users')
    adminUsers.value = res.data.users || []
  }

  async function createUser(username, password) {
    const res = await api.post('/api/admin/users', { username, password })
    await fetchAdminUsers()
    return res.data
  }

  async function deleteUser(userId) {
    await api.delete(`/api/admin/users/${userId}`)
    await fetchAdminUsers()
  }

  async function modifyCoins(userId, amount) {
    const res = await api.post(`/api/admin/users/${userId}/coins`, { amount })
    await fetchAdminUsers()
    return res.data
  }

  async function fetchPendingSettlements() {
    const res = await api.get('/api/admin/settlements', { params: { status: 'pending' } })
    pendingSettlements.value = res.data.pending || []
  }

  async function confirmSettlement(matchId) {
    const res = await api.post('/api/admin/settlements/confirm', { match_id: matchId })
    await fetchPendingSettlements()
    return res.data
  }

  async function cancelMatch(matchId) {
    const res = await api.post(`/api/admin/matches/${matchId}/cancel`)
    await fetchPendingSettlements()
    return res.data
  }

  async function fetchAdminAccounts() {
    const res = await api.get('/api/admin/admins')
    adminAccounts.value = res.data.admins || []
  }

  async function createAdmin(username, password) {
    const res = await api.post('/api/admin/admins', { username, password })
    await fetchAdminAccounts()
    return res.data
  }

  async function deleteAdmin(adminId) {
    await api.delete(`/api/admin/admins/${adminId}`)
    await fetchAdminAccounts()
  }

  async function fetchLogs(page = 1) {
    const res = await api.get('/api/admin/logs', { params: { page, per_page: 30 } })
    operationLogs.value = res.data.logs || []
    return res.data
  }

  async function fetchStats(dateFrom, dateTo) {
    const res = await api.get('/api/admin/stats', { params: { date_from: dateFrom, date_to: dateTo } })
    return res.data
  }

  return {
    isLoggedIn, isAdminLoggedIn, isSuperAdmin, user, token,
    matches, matchDetail, oddsCache, myBets, transactions, loading,
    adminUsers, adminAccounts, pendingSettlements, operationLogs,
    getMatchStatusText, getBetStatusText, getMarketName, getSelectionLabel,
    formatMatchTime, formatDate,
    loginUser, loginAdmin, restoreSession, logout, changePassword,
    fetchMatches, fetchMatchDetail, getMatchById, getOdds, placeBet,
    fetchMyBets, fetchTransactions, fetchProfile,
    fetchAdminUsers, createUser, deleteUser, modifyCoins,
    fetchPendingSettlements, confirmSettlement, cancelMatch,
    fetchAdminAccounts, createAdmin, deleteAdmin,
    fetchLogs, fetchStats,
    getMockMatches,
  }
})
