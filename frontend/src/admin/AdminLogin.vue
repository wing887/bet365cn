<template>
  <div class="admin-login">
    <div class="bg_login">
      <!-- Header: Clear admin label -->
      <div class="box_language" style="font-weight:600;letter-spacing:2px;">管理员登录入口</div>

      <!-- Login Form -->
      <div class="box_login">
        <label id="usr_lab" :class="usrLabClass">
          <input id="usr" class="userid" type="text" autocomplete="off" required
                 v-model="username" @input="error=''" @focus="usrFocused=true" @blur="usrFocused=false;usrTouched=true">
          <span class="text_input" data-tooltip="管理员账号"></span>
          <i class="btn_clear" @click="username='';usrFocused=false;error=''">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="m8 7.2 6-6c.2-.2.6-.2.8 0s.2.6 0 .8l-6 6 6 6c.2.2.2.6 0 .8s-.6.2-.8 0l-6-6-6 6c-.2.2-.6.2-.8 0s-.2-.6 0-.8l6-6-6-6c-.2-.2-.2-.6 0-.8s.6-.2.8 0l6 6z" fill-rule="evenodd" clip-rule="evenodd" fill-opacity=".4"/></svg>
          </i>
        </label>

        <label id="pwd_lab" :class="pwdLabClass">
          <input id="pwd" type="password" autocomplete="off" required
                 v-model="password" @input="error=''" @focus="pwdFocused=true" @blur="pwdFocused=false;pwdTouched=true"
                 @keyup.enter="doLogin">
          <span class="text_input" data-tooltip="管理密码"></span>
          <i class="btn_clear" @click="password='';pwdFocused=false;error=''">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="m8 7.2 6-6c.2-.2.6-.2.8 0s.2.6 0 .8l-6 6 6 6c.2.2.2.6 0 .8s-.6.2-.8 0l-6-6-6 6c-.2.2-.6.2-.8 0s-.2-.6 0-.8l6-6-6-6c-.2-.2-.2-.6 0-.8s.6-.2.8 0l6 6z" fill-rule="evenodd" clip-rule="evenodd" fill-opacity=".4"/></svg>
          </i>
        </label>

        <span class="text_error" :style="{display:error?'block':'none'}">{{ error }}</span>

        <input class="btn_login" type="button" :value="loading?'登录中...':'管理员登入'"
               :disabled="loading" @click="doLogin">

        <div style="text-align:center;margin-top:12px;">
          <router-link to="/login" style="font-size:14px;color:#0066CC;text-decoration:none;">用户登录 →</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const usrFocused = ref(false)
const pwdFocused = ref(false)
const usrTouched = ref(false)
const pwdTouched = ref(false)

const usrLabClass = computed(() => ({
  lab_input: true,
  on: usrFocused.value || username.value,
  error: usrTouched.value && error.value && !username.value
}))
const pwdLabClass = computed(() => ({
  lab_input: true,
  on: pwdFocused.value || password.value,
  error: pwdTouched.value && error.value && !password.value
}))

async function doLogin() {
  error.value = ''
  usrTouched.value = pwdTouched.value = true

  if (!username.value || !password.value) {
    error.value = !username.value ? '请输入管理员账号' : '请输入管理密码'
    return
  }

  loading.value = true
  try {
    await store.loginAdmin(username.value, password.value)
    router.push('/admin')
  } catch (e) {
    error.value = e.response?.data?.error || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style>
.admin-login .bg_login {
  background: #f5f5f5; width: 100%; min-height: 100dvh;
  display: flex; flex-direction: column; align-items: center;
  padding-bottom: 16px;
}
.admin-login .box_language {
  width: 100%; height: 56px; line-height: 56px; text-align: center;
  font-size: 14px; color: #fff; background: #503f32;
}
.admin-login .box_login {
  width: 100%; max-width: 320px; margin: 16px auto;
  padding: 24px 16px 16px; text-align: center; background: #fff;
}
.admin-login .lab_input { position: relative; display: block; width: 100%; height: 48px; margin-bottom: 16px; }
.admin-login .lab_input > input {
  display: block; width: 100%; height: 100%; margin: 0; padding: 0 32px 0 16px;
  font-size: 16px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.32);
  color: #000; box-shadow: none; transition: all 0.3s ease;
  pointer-events: auto; background: #fff; outline: none;
}
.admin-login .userid { font-family: 'Tahoma','Verdana',serif; }
.admin-login .text_input { line-height: normal !important; pointer-events: none; }
.admin-login .text_input::after {
  content: attr(data-tooltip); position: absolute; top: 0; left: 14px;
  display: flex; height: 100%; align-items: center; padding: 0 4px;
  font-size: 16px; color: rgba(0,0,0,0.24); background: #fff0;
  transition: all 0.3s ease, background 0.1s 0.1s;
}
.admin-login .lab_input > input:valid ~ .text_input::after {
  top: -8px; height: 16px; font-size: 12px; color: rgba(0,0,0,0.56); background: #fff;
}
.admin-login .lab_input.on > input { border: 2px solid #19805c; }
.admin-login .lab_input.on .text_input::after {
  top: -8px; height: 16px; font-size: 12px; color: #19805c !important; background: #fff;
}
.admin-login .lab_input.error > input { border: 2px solid #e76565 !important; }
.admin-login .lab_input.error.on > input { border: 2px solid #e76565 !important; }
.admin-login .lab_input.error .text_input::after,
.admin-login .lab_input.on.error .text_input::after { color: #e76565 !important; }
.admin-login .lab_input .btn_clear {
  position: absolute; top: 8px; right: 8px; width: 32px; height: 32px; padding: 8px;
  z-index: -1; cursor: default; pointer-events: auto; transition: none !important;
}
.admin-login .lab_input .btn_clear svg {
  width: 100%; height: 100%; opacity: 0; fill: rgba(0,0,0,0.4); pointer-events: none;
}
.admin-login .lab_input.on > input:valid ~ .btn_clear { z-index: 1; cursor: pointer; }
.admin-login .text_error {
  display: none; width: 100%; line-height: 16px; margin-bottom: 16px;
  text-align: center; font-size: 12px; color: #ce3636;
}
.admin-login .btn_login {
  width: 100%; height: 48px; line-height: 48px; margin-bottom: 8px;
  padding: 0 16px; border-radius: 4px; text-align: center; font-size: 12px;
  font-weight: bold; border: none; color: #fff; background: #19805c;
  transition: background 0.3s ease; cursor: pointer;
}
.admin-login .btn_login:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
