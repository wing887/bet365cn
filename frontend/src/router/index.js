import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/Home.vue'), meta: { title: 'HGN' } },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { title: '登录' } },
  { path: '/sport/:sport/:period', name: 'sport', component: () => import('../views/SportList.vue'), meta: { title: '赛事' } },
  { path: '/match/:id', name: 'match', component: () => import('../views/MatchDetail.vue'), meta: { title: '比赛详情' } },
  { path: '/my-bets', name: 'bets', component: () => import('../views/MyBets.vue'), meta: { title: '投注记录' } },
  { path: '/my-events', name: 'events', component: () => import('../views/MyEvents.vue'), meta: { title: '我的赛事' } },
  { path: '/profile', name: 'profile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心' } },
  // Admin
  { path: '/dabiaoge', name: 'adminLogin', component: () => import('../admin/AdminLogin.vue'), meta: { title: '管理员登录' } },
  { path: '/admin', name: 'admin', component: () => import('../admin/Dashboard.vue'), meta: { title: '管理后台' } },
  { path: '/admin/users', name: 'adminUsers', component: () => import('../admin/UserManage.vue'), meta: { title: '用户管理' } },
  { path: '/admin/coins', name: 'adminCoins', component: () => import('../admin/CoinManage.vue'), meta: { title: '金币操作' } },
  { path: '/admin/settlements', name: 'adminSettlements', component: () => import('../admin/Settlement.vue'), meta: { title: '结算管理' } },
  { path: '/admin/bet-limits', name: 'adminBetLimits', component: () => import('../admin/BetLimitConfig.vue'), meta: { title: '投注限额' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() { return { top: 0 } }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'HGN'
  const hasToken = !!localStorage.getItem('token')
  const isUser = !!localStorage.getItem('user')
  const isAdminUser = !!localStorage.getItem('admin_user')

  if (to.path.startsWith('/admin') && !(hasToken && isAdminUser)) {
    if (to.path !== '/dabiaoge') return next('/dabiaoge')
  }
  next()
})

export default router
