import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // --- Auth state (mock) ---
  const isLoggedIn = ref(true)  // 默认已登录方便预览
  const isAdminLoggedIn = ref(false)
  const isSuperAdmin = ref(false)
  const user = ref({
    id: 1,
    username: 'user001',
    nickname: '用户001',
    coin_balance: 5000
  })

  // --- Matches mock data ---
  const matches = ref([
    { id: 1, event_id: 'evt001', home_team: '曼城', away_team: '阿森纳', league_name: '英格兰 - 英超', league_slug: 'england-premier-league', match_date: '2026-05-19T19:00:00Z', status: 'pending', scores_home: 0, scores_away: 0 },
    { id: 2, event_id: 'evt002', home_team: '拜仁慕尼黑', away_team: '多特蒙德', league_name: '德国 - 德甲', league_slug: 'germany-bundesliga', match_date: '2026-05-19T19:30:00Z', status: 'live', scores_home: 1, scores_away: 0 },
    { id: 3, event_id: 'evt003', home_team: '皇家马德里', away_team: '巴塞罗那', league_name: '西班牙 - 西甲', league_slug: 'spain-laliga', match_date: '2026-05-19T18:00:00Z', status: 'settled', scores_home: 3, scores_away: 1 },
    { id: 4, event_id: 'evt004', home_team: '尤文图斯', away_team: '国际米兰', league_name: '意大利 - 意甲', league_slug: 'italy-serie-a', match_date: '2026-05-19T20:00:00Z', status: 'pending', scores_home: 0, scores_away: 0 },
    { id: 5, event_id: 'evt005', home_team: '巴黎圣日耳曼', away_team: '里昂', league_name: '法国 - 法甲', league_slug: 'france-ligue-1', match_date: '2026-05-19T20:00:00Z', status: 'pending', scores_home: 0, scores_away: 0 },
    { id: 6, event_id: 'evt006', home_team: '利物浦', away_team: '切尔西', league_name: '英格兰 - 英超', league_slug: 'england-premier-league', match_date: '2026-05-19T21:00:00Z', status: 'pending', scores_home: 0, scores_away: 0 },
    { id: 7, event_id: 'evt007', home_team: 'AC米兰', away_team: '那不勒斯', league_name: '意大利 - 意甲', league_slug: 'italy-serie-a', match_date: '2026-05-19T18:30:00Z', status: 'settled', scores_home: 2, scores_away: 2 },
    { id: 8, event_id: 'evt008', home_team: '马德里竞技', away_team: '塞维利亚', league_name: '西班牙 - 西甲', league_slug: 'spain-laliga', match_date: '2026-05-19T19:00:00Z', status: 'live', scores_home: 0, scores_away: 1 },
  ])

  // --- Odds mock ---
  const odds = ref({
    1: {  // Man City vs Arsenal
      ML: { bookmaker: 'Bet365', home: 1.65, draw: 4.20, away: 4.80 },
      Spread: { bookmaker: 'Bet365', hdp: 0.75, home: 1.92, away: 1.98 },
      Totals: { bookmaker: 'Bet365', hdp: 2.75, over: 1.85, under: 2.05 },
      CS: { bookmaker: 'Bet365', scores: [
        { label: '1-1', odds: 7.50 }, { label: '1-0', odds: 8.00 },
        { label: '2-1', odds: 8.50 }, { label: '0-0', odds: 10.00 },
        { label: '2-0', odds: 11.00 }, { label: '0-1', odds: 13.00 },
        { label: '3-1', odds: 15.00 }, { label: '1-2', odds: 17.00 },
        { label: '3-0', odds: 21.00 }, { label: '2-2', odds: 23.00 }
      ]}
    },
    2: {  // Bayern vs Dortmund
      ML: { bookmaker: 'Bet365', home: 1.50, draw: 4.50, away: 5.50 },
      Spread: { bookmaker: 'Bet365', hdp: 1.0, home: 1.85, away: 2.05 },
      Totals: { bookmaker: 'Bet365', hdp: 3.25, over: 1.90, under: 2.00 },
      CS: { bookmaker: 'Bet365', scores: [
        { label: '2-1', odds: 8.00 }, { label: '1-0', odds: 7.00 },
        { label: '2-0', odds: 7.50 }, { label: '3-1', odds: 10.00 },
        { label: '1-1', odds: 8.50 }, { label: '3-0', odds: 12.00 },
        { label: '0-0', odds: 15.00 }, { label: '2-2', odds: 17.00 },
        { label: '3-2', odds: 21.00 }, { label: '1-2', odds: 23.00 }
      ]}
    },
    4: {  // Juve vs Inter
      ML: { bookmaker: 'Bet365', home: 2.80, draw: 3.20, away: 2.60 },
      Spread: { bookmaker: 'Bet365', hdp: 0, home: 1.95, away: 1.95 },
      Totals: { bookmaker: 'Bet365', hdp: 2.25, over: 1.88, under: 2.02 },
      CS: { bookmaker: 'Bet365', scores: [
        { label: '1-1', odds: 6.50 }, { label: '1-0', odds: 7.50 },
        { label: '0-0', odds: 8.50 }, { label: '0-1', odds: 8.00 },
        { label: '2-1', odds: 9.50 }, { label: '1-2', odds: 10.00 },
        { label: '2-0', odds: 14.00 }, { label: '0-2', odds: 15.00 },
        { label: '2-2', odds: 17.00 }, { label: '3-1', odds: 23.00 }
      ]}
    },
    5: {  // PSG vs Lyon
      ML: { bookmaker: 'Bet365', home: 1.35, draw: 5.00, away: 8.00 },
      Spread: { bookmaker: 'Bet365', hdp: 1.25, home: 1.80, away: 2.10 },
      Totals: { bookmaker: 'Bet365', hdp: 3.0, over: 1.75, under: 2.15 },
      CS: { bookmaker: 'Bet365', scores: [
        { label: '2-0', odds: 6.00 }, { label: '3-0', odds: 7.00 },
        { label: '2-1', odds: 8.00 }, { label: '1-0', odds: 9.00 },
        { label: '3-1', odds: 9.50 }, { label: '4-0', odds: 11.00 },
        { label: '1-1', odds: 13.00 }, { label: '4-1', odds: 15.00 },
        { label: '0-0', odds: 21.00 }, { label: '3-2', odds: 26.00 }
      ]}
    },
    6: {  // Liverpool vs Chelsea
      ML: { bookmaker: 'Bet365', home: 1.95, draw: 3.60, away: 3.80 },
      Spread: { bookmaker: 'Bet365', hdp: 0.5, home: 2.00, away: 1.90 },
      Totals: { bookmaker: 'Bet365', hdp: 2.5, over: 1.82, under: 2.08 },
      CS: { bookmaker: 'Bet365', scores: [
        { label: '1-1', odds: 7.00 }, { label: '2-1', odds: 8.50 },
        { label: '1-0', odds: 8.00 }, { label: '0-0', odds: 10.00 },
        { label: '2-0', odds: 12.00 }, { label: '0-1', odds: 11.00 },
        { label: '1-2', odds: 13.00 }, { label: '3-1', odds: 17.00 },
        { label: '2-2', odds: 19.00 }, { label: '0-2', odds: 23.00 }
      ]}
    },
  })

  // --- My bets mock ---
  const myBets = ref([
    { id: 1, match_home: '皇家马德里', match_away: '巴塞罗那', league: '西甲', market_type: 'ML', market_name: '胜平负', selection: '主胜', selection_label: '主胜', odds: 1.65, bet_amount: 200, potential_win: 330, status: 'won', result: '+330', settled_at: '2026-05-19 20:30' },
    { id: 2, match_home: '皇家马德里', match_away: '巴塞罗那', league: '西甲', market_type: 'Totals', market_name: '大小球', selection: 'over', selection_label: '大 2.75', odds: 1.85, bet_amount: 100, potential_win: 185, status: 'won', result: '+185', settled_at: '2026-05-19 20:30' },
    { id: 3, match_home: 'AC米兰', match_away: '那不勒斯', league: '意甲', market_type: 'ML', market_name: '胜平负', selection: 'draw', selection_label: '平局', odds: 3.40, bet_amount: 50, potential_win: 170, status: 'lost', result: '-50', settled_at: '2026-05-19 21:00' },
    { id: 4, match_home: '曼城', match_away: '阿森纳', league: '英超', market_type: 'ML', market_name: '胜平负', selection: 'home', selection_label: '主胜', odds: 1.65, bet_amount: 300, potential_win: 495, status: 'pending', result: '---', settled_at: null },
    { id: 5, match_home: '曼城', match_away: '阿森纳', league: '英超', market_type: 'CS', market_name: '波胆', selection: '2-1', selection_label: '2-1', odds: 8.50, bet_amount: 50, potential_win: 425, status: 'pending', result: '---', settled_at: null },
    { id: 6, match_home: '拜仁慕尼黑', match_away: '多特蒙德', league: '德甲', market_type: 'ML', market_name: '胜平负', selection: 'home', selection_label: '主胜', odds: 1.50, bet_amount: 200, potential_win: 300, status: 'pending', result: '---', settled_at: null },
  ])

  // --- Coin transactions mock ---
  const transactions = ref([
    { id: 1, amount: 10000, type: 'admin_add', note: '管理员充值', created_at: '2026-05-18 10:00' },
    { id: 2, amount: -200, type: 'bet_place', note: '下注: 皇马vs巴萨 胜平负-主胜', created_at: '2026-05-19 17:30' },
    { id: 3, amount: -100, type: 'bet_place', note: '下注: 皇马vs巴萨 大小球-大球', created_at: '2026-05-19 17:31' },
    { id: 4, amount: -50, type: 'bet_place', note: '下注: AC米兰vs那不勒斯 胜平负-平局', created_at: '2026-05-19 18:00' },
    { id: 5, amount: 330, type: 'bet_win', note: '中奖: 皇马vs巴萨 胜平负-主胜', created_at: '2026-05-19 20:30' },
    { id: 6, amount: 185, type: 'bet_win', note: '中奖: 皇马vs巴萨 大小球-大球', created_at: '2026-05-19 20:30' },
    { id: 7, amount: -300, type: 'bet_place', note: '下注: 曼城vs阿森纳 胜平负-主胜', created_at: '2026-05-19 19:00' },
    { id: 8, amount: -50, type: 'bet_place', note: '下注: 曼城vs阿森纳 波胆-2:1', created_at: '2026-05-19 19:01' },
    { id: 9, amount: -200, type: 'bet_place', note: '下注: 拜仁vs多特 胜平负-主胜', created_at: '2026-05-19 19:15' },
    { id: 10, amount: 500, type: 'admin_add', note: '管理员充值', created_at: '2026-05-19 10:00' },
  ])

  // --- Admin mock data ---
  const adminUsers = ref([
    { id: 1, username: 'user001', nickname: '用户001', coin_balance: 5000, status: 'active', created_at: '2026-05-01' },
    { id: 2, username: 'user002', nickname: '用户002', coin_balance: 2000, status: 'active', created_at: '2026-05-02' },
    { id: 3, username: 'user003', nickname: '用户003', coin_balance: 800, status: 'active', created_at: '2026-05-03' },
    { id: 4, username: 'user004', nickname: '用户004', coin_balance: 15000, status: 'disabled', created_at: '2026-05-04' },
  ])

  const adminAccounts = ref([
    { id: 1, username: 'superadmin', role: 'super_admin', created_at: '2026-05-01' },
    { id: 2, username: 'admin01', role: 'admin', created_at: '2026-05-02' },
  ])

  const pendingSettlements = ref([
    { id: 1, match_home: '拜仁慕尼黑', match_away: '多特蒙德', scores: '1:0', league: '德甲', total_bets: 22, total_users: 15, total_payout: 3800, status: 'pending' },
    { id: 2, match_home: '马德里竞技', match_away: '塞维利亚', scores: '0:1', league: '西甲', total_bets: 8, total_users: 6, total_payout: 1200, status: 'pending' },
  ])

  const operationLogs = ref([
    { id: 1, admin_name: 'superadmin', action: '金币操作', target: 'user001', detail: '充值 +10000', created_at: '2026-05-18 10:00' },
    { id: 2, admin_name: 'admin01', action: '金币操作', target: 'user002', detail: '充值 +5000', created_at: '2026-05-18 14:30' },
    { id: 3, admin_name: 'superadmin', action: '结算确认', target: '皇马vs巴萨', detail: '确认结算 15注/12用户', created_at: '2026-05-19 20:31' },
    { id: 4, admin_name: 'superadmin', action: '创建用户', target: 'user003', detail: '创建账号', created_at: '2026-05-03 09:00' },
    { id: 5, admin_name: 'admin01', action: '金币扣减', target: 'user004', detail: '扣减 -3000', created_at: '2026-05-15 16:00' },
    { id: 6, admin_name: 'superadmin', action: '创建管理员', target: 'admin01', detail: '创建普通管理员', created_at: '2026-05-02 11:00' },
  ])

  // --- Helper functions ---
  function getMatchById(id) {
    return matches.value.find(m => m.id === Number(id))
  }

  function getOdds(matchId) {
    return odds.value[matchId] || null
  }

  function getMatchStatusText(status) {
    const map = { pending: '即将开始', live: '进行中', settled: '已结束', cancelled: '已取消' }
    return map[status] || status
  }

  function getBetStatusText(status) {
    const map = { pending: '待结算', won: '已赢', lost: '已输', push: '走水', refunded: '已退款' }
    return map[status] || status
  }

  function formatDate(iso) {
    if (!iso) return '---'
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
  }

  function formatMatchTime(iso) {
    if (!iso) return '---'
    const d = new Date(iso)
    const now = new Date()
    if (d.toDateString() === now.toDateString()) {
      return '今天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
    }
    return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  // --- Actions (mock) ---
  function placeBet(matchId, marketType, selection, amount) {
    const match = getMatchById(matchId)
    const o = getOdds(matchId)
    let oddValue = 0
    let selectionLabel = selection

    if (marketType === 'ML') {
      oddValue = o.ML[selection]
      const labels = { home: '主胜', draw: '平局', away: '客胜' }
      selectionLabel = labels[selection]
    } else if (marketType === 'Spread') {
      oddValue = o.Spread[selection]
      selectionLabel = selection === 'home' ? '主队赢盘' : '客队赢盘'
    } else if (marketType === 'Totals') {
      oddValue = o.Totals[selection]
      selectionLabel = selection === 'over' ? `大 ${o.Totals.hdp}` : `小 ${o.Totals.hdp}`
    } else if (marketType === 'CS') {
      const cs = o.CS.scores.find(s => s.label === selection)
      oddValue = cs ? cs.odds : 0
    }

    if (amount < 50) return { success: false, msg: '最低下注50金币' }
    if (amount > user.value.coin_balance) return { success: false, msg: '金币不足' }

    user.value.coin_balance -= amount
    const win = Math.round(amount * oddValue)
    myBets.value.unshift({
      id: Date.now(),
      match_home: match.home_team,
      match_away: match.away_team,
      league: match.league_name,
      market_type: marketType,
      market_name: { ML: '胜平负', Spread: '让球盘', Totals: '大小球', CS: '波胆' }[marketType],
      selection,
      selection_label: selectionLabel,
      odds: oddValue,
      bet_amount: amount,
      potential_win: win,
      status: 'pending',
      result: '---',
      settled_at: null
    })
    return { success: true, msg: '下注成功', odd: oddValue, win }
  }

  function addCoins(userId, amount) {
    const u = adminUsers.value.find(x => x.id === userId)
    if (u) u.coin_balance += amount
  }

  return {
    isLoggedIn, isAdminLoggedIn, isSuperAdmin, user,
    matches, odds, myBets, transactions,
    adminUsers, adminAccounts, pendingSettlements, operationLogs,
    getMatchById, getOdds, getMatchStatusText, getBetStatusText, formatDate, formatMatchTime,
    placeBet, addCoins,
  }
})
