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
import Logs from '../admin/Logs.vue'
import Stats from '../admin/Stats.vue'

const routes = [
  { path: '/', name: 'home', component: Home, meta: { title: 'bet365cn' } },
  { path: '/match/:id', name: 'match', component: MatchDetail, meta: { title: '比赛详情' } },
  { path: '/my-bets', name: 'bets', component: MyBets, meta: { title: '我的下注' } },
  { path: '/my-coins', name: 'coins', component: MyCoins, meta: { title: '金币记录' } },
  { path: '/login', name: 'login', component: Login, meta: { title: '登录' } },
  { path: '/profile', name: 'profile', component: Profile, meta: { title: '个人中心' } },
  { path: '/admin/login', name: 'adminLogin', component: AdminLogin, meta: { title: '管理员登录' } },
  { path: '/admin', name: 'admin', component: Dashboard, meta: { title: '管理后台' } },
  { path: '/admin/users', name: 'adminUsers', component: UserManage, meta: { title: '用户管理' } },
  { path: '/admin/coins', name: 'adminCoins', component: CoinManage, meta: { title: '金币操作' } },
  { path: '/admin/settlements', name: 'adminSettlements', component: Settlement, meta: { title: '结算管理' } },
  { path: '/admin/admins', name: 'adminAdmins', component: AdminManage, meta: { title: '管理员管理' } },
  { path: '/admin/logs', name: 'adminLogs', component: Logs, meta: { title: '操作日志' } },
  { path: '/admin/stats', name: 'adminStats', component: Stats, meta: { title: '金币统计' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  document.title = to.meta.title || 'bet365cn'
})

export default router
