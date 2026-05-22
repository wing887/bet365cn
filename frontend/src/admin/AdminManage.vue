<template>
  <div class="admin-page">
    <router-link to="/admin" class="back-link">← 返回后台</router-link>
    <div class="page-title">
      {{ store.canCreateAdmin ? '管理员管理' : '代理管理' }}
    </div>

    <!-- 创建表单 -->
    <div class="card form-card">
      <div class="form-title">
        {{ store.canCreateAdmin ? '创建管理员/代理' : '创建代理' }}
      </div>
      <div class="form-row">
        <input v-model="newAdminUser" class="input" placeholder="账号" />
        <input v-model="newAdminPwd" class="input" placeholder="密码" />
        <select v-if="store.canCreateAdmin" v-model="newAdminRole" class="input select-role">
          <option value="admin">管理</option>
          <option value="agent">代理</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="createAdmin">创建</button>
      </div>
    </div>

    <!-- 管理员列表 -->
    <div class="card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>账号</th>
              <th>角色</th>
              <th>余额</th>
              <th>状态</th>
              <th>最后登录</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in store.adminAccounts" :key="a.id">
              <td class="td-username">{{ a.username }}</td>
              <td>
                <span :class="'role-tag role-' + a.role">
                  {{ a.role === 'super_admin' ? '超管' : a.role === 'admin' ? '管理' : '代理' }}
                </span>
              </td>
              <td v-if="a.role === 'agent'" class="td-coins">{{ a.coin_balance }}</td>
              <td v-else class="td-time">—</td>
              <td>
                <span :class="'tag ' + (a.status === 'active' ? 'tag-green' : 'tag-red')">
                  {{ a.status === 'active' ? '活跃' : '封禁' }}
                </span>
              </td>
              <td class="td-time">{{ store.formatDate(a.last_login_at) }}</td>
              <td>
                <div class="action-btns" v-if="a.role !== 'super_admin'">
                  <!-- 代理充值/扣减（超管+管理） -->
                  <button
                    v-if="a.role === 'agent' && store.canCreateAgent"
                    class="btn btn-accent btn-xs"
                    @click="showRecharge(a)"
                  >充值</button>
                  <!-- 封禁/解封 -->
                  <button
                    v-if="a.status === 'active'"
                    class="btn btn-warn btn-xs"
                    @click="doBan(a.id, true)"
                  >封禁</button>
                  <button
                    v-if="a.status === 'disabled'"
                    class="btn btn-green btn-xs"
                    @click="doBan(a.id, false)"
                  >解封</button>
                  <!-- 删除 -->
                  <button class="btn btn-danger btn-xs" @click="doDelete(a.id)">删除</button>
                </div>
                <span v-else class="td-time">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 充值弹窗 -->
    <div v-if="rechargeTarget" class="modal-overlay" @click.self="rechargeTarget = null">
      <div class="modal-card">
        <div class="modal-title">
          给 {{ rechargeTarget.username }} {{ rechargeTarget.coin_balance >= 0 ? '充值/扣减' : '' }}
        </div>
        <div class="modal-body">
          <div class="recharge-info">当前余额：{{ rechargeTarget.coin_balance }} 金币</div>
          <div class="form-row" style="margin-top: 10px;">
            <input v-model.number="rechargeAmount" type="number" class="input" placeholder="正=加 负=扣" />
            <button class="btn btn-primary btn-sm" @click="doRecharge">确认</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const showToast = inject('showToast')
const newAdminUser = ref('')
const newAdminPwd = ref('')
const newAdminRole = ref('agent')
const rechargeTarget = ref(null)
const rechargeAmount = ref(0)

async function createAdmin() {
  if (!newAdminUser.value || !newAdminPwd.value) {
    showToast('请填写账号和密码', 'error')
    return
  }
  try {
    await store.createAdmin(newAdminUser.value, newAdminPwd.value, newAdminRole.value)
    showToast('创建成功')
    newAdminUser.value = ''
    newAdminPwd.value = ''
  } catch (e) {
    showToast(e.response?.data?.error || '创建失败', 'error')
  }
}

function showRecharge(agent) {
  rechargeTarget.value = agent
  rechargeAmount.value = 0
}

async function doRecharge() {
  if (!rechargeAmount.value) {
    showToast('请输入金额', 'error')
    return
  }
  try {
    await store.rechargeAgent(rechargeTarget.value.id, rechargeAmount.value)
    showToast(`${rechargeAmount.value > 0 ? '充值' : '扣减'}成功`)
    rechargeTarget.value = null
  } catch (e) {
    showToast(e.response?.data?.error || '操作失败', 'error')
  }
}

async function doBan(id, ban) {
  try {
    await store.banAdmin(id, ban)
    showToast(ban ? '已封禁' : '已解封')
  } catch (e) {
    showToast(e.response?.data?.error || '操作失败', 'error')
  }
}

async function doDelete(id) {
  if (!confirm('确定删除？')) return
  try {
    await store.deleteAdmin(id)
    showToast('已删除')
  } catch (e) {
    showToast(e.response?.data?.error || '删除失败', 'error')
  }
}

onMounted(async () => {
  await store.fetchAdminAccounts()
})
</script>
