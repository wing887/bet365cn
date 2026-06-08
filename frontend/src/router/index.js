import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/Home.vue'), meta: { title: 'bet365cn', requiresAuth: true } },
  { path: '/match/:id', name: 'match', component: () => import('../views/MatchDetail.vue'), meta: { title: '比赛详情', requiresAuth: true } },
  { path: '/my-bets', name: 'bets', component: () => import('../views/MyBets.vue'), meta: { title: '我的下注', requiresAuth: true } },
  { path: '/my-coins', name: 'coins', component: () => import('../views/MyCoins.vue'), meta: { title: '金币记录', requiresAuth: true } },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { title: '登录' } },
  { path: '/profile', name: 'profile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心', requiresAuth: true } },
  { path: '/admin/login', name: 'adminLogin', component: () => import('../admin/AdminLogin.vue'), meta: { title: '管理员登录' } },
  { path: '/admin', name: 'admin', component: () => import('../admin/Dashboard.vue'), meta: { title: '管理后台', requiresAdmin: true } },
  { path: '/admin/users', name: 'adminUsers', component: () => import('../admin/UserManage.vue'), meta: { title: '用户管理', requiresAdmin: true } },
  { path: '/admin/coins', name: 'adminCoins', component: () => import('../admin/CoinManage.vue'), meta: { title: '金币操作', requiresAdmin: true } },
  { path: '/admin/settlements', name: 'adminSettlements', component: () => import('../admin/Settlement.vue'), meta: { title: '结算管理', requiresAdmin: true } },
  { path: '/admin/admins', name: 'adminAdmins', component: () => import('../admin/AdminManage.vue'), meta: { title: '管理员管理', requiresAdmin: true } },
  { path: '/admin/agents', name: 'adminAgents', component: () => import('../admin/AgentManage.vue'), meta: { title: '代理管理', requiresAdmin: true } },
  { path: '/admin/logs', name: 'adminLogs', component: () => import('../admin/Logs.vue'), meta: { title: '操作日志', requiresAdmin: true } },
  { path: '/admin/stats', name: 'adminStats', component: () => import('../admin/Stats.vue'), meta: { title: '金币统计', requiresAdmin: true } },
  { path: '/admin/customers', name: 'agentCustomers', component: () => import('../admin/CustomerStats.vue'), meta: { title: '客户统计', requiresAdmin: true } },
  { path: '/admin/bet-limits', name: 'adminBetLimits', component: () => import('../admin/BetLimitConfig.vue'), meta: { title: '投注限额', requiresAdmin: true } },
  { path: '/admin/market-status', name: 'adminMarketStatus', component: () => import('../admin/MarketStatus.vue'), meta: { title: '封盘管理', requiresAdmin: true } },
  { path: '/admin/match-bets', name: 'adminMatchBets', component: () => import('../admin/MatchBets.vue'), meta: { title: '下注核对', requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'bet365cn'

  const hasToken = !!localStorage.getItem('token')
  const isUser = !!localStorage.getItem('user')
  const isAdminUser = !!localStorage.getItem('admin_user')

  if (to.meta.requiresAuth && !(hasToken && isUser)) {
    return next('/login')
  }

  if (to.meta.requiresAdmin && !(hasToken && isAdminUser)) {
    return next('/admin/login')
  }

  if (to.path === '/login' && hasToken && isUser) {
    return next('/')
  }
  if (to.path === '/admin/login' && hasToken && isAdminUser) {
    return next('/admin')
  }

  next()
})

export default router
