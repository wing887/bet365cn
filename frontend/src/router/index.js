import { createRouter, createWebHashHistory } from 'vue-router'

import Home from '../views/Home.vue'
import MatchDetail from '../views/MatchDetail.vue'
import MyBets from '../views/MyBets.vue'
import MyCoins from '../views/MyCoins.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'

import AdminLogin from '../admin/AdminLogin.vue'
import Dashboard from '../admin/Dashboard.vue'
import UserManage from '../admin/UserManage.vue'
import CoinManage from '../admin/CoinManage.vue'
import Settlement from '../admin/Settlement.vue'
import AdminManage from '../admin/AdminManage.vue'
import AgentManage from '../admin/AgentManage.vue'
import Logs from '../admin/Logs.vue'
import Stats from '../admin/Stats.vue'
import CustomerStats from '../admin/CustomerStats.vue'
import BetLimitConfig from '../admin/BetLimitConfig.vue'
import MarketStatus from '../admin/MarketStatus.vue'

const routes = [
  { path: '/', name: 'home', component: Home, meta: { title: 'bet365cn', requiresAuth: true } },
  { path: '/match/:id', name: 'match', component: MatchDetail, meta: { title: '比赛详情', requiresAuth: true } },
  { path: '/my-bets', name: 'bets', component: MyBets, meta: { title: '我的下注', requiresAuth: true } },
  { path: '/my-coins', name: 'coins', component: MyCoins, meta: { title: '金币记录', requiresAuth: true } },
  { path: '/login', name: 'login', component: Login, meta: { title: '登录' } },
  { path: '/profile', name: 'profile', component: Profile, meta: { title: '个人中心', requiresAuth: true } },
  { path: '/admin/login', name: 'adminLogin', component: AdminLogin, meta: { title: '管理员登录' } },
  { path: '/admin', name: 'admin', component: Dashboard, meta: { title: '管理后台', requiresAdmin: true } },
  { path: '/admin/users', name: 'adminUsers', component: UserManage, meta: { title: '用户管理', requiresAdmin: true } },
  { path: '/admin/coins', name: 'adminCoins', component: CoinManage, meta: { title: '金币操作', requiresAdmin: true } },
  { path: '/admin/settlements', name: 'adminSettlements', component: Settlement, meta: { title: '结算管理', requiresAdmin: true } },
  { path: '/admin/admins', name: 'adminAdmins', component: AdminManage, meta: { title: '管理员管理', requiresAdmin: true } },
  { path: '/admin/agents', name: 'adminAgents', component: AgentManage, meta: { title: '代理管理', requiresAdmin: true } },
  { path: '/admin/logs', name: 'adminLogs', component: Logs, meta: { title: '操作日志', requiresAdmin: true } },
  { path: '/admin/stats', name: 'adminStats', component: Stats, meta: { title: '金币统计', requiresAdmin: true } },
  { path: '/admin/customers', name: 'agentCustomers', component: CustomerStats, meta: { title: '客户统计', requiresAdmin: true } },
  { path: '/admin/bet-limits', name: 'adminBetLimits', component: BetLimitConfig, meta: { title: '投注限额', requiresAdmin: true } },
  { path: '/admin/market-status', name: 'adminMarketStatus', component: MarketStatus, meta: { title: '封盘管理', requiresAdmin: true } },
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
