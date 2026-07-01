<template>
  <div class="login">
    <div class="bg_login">
      <!-- Language Switcher -->
      <div class="box_language">
        <span :class="['btn_language', { on: lang === 'cn' }]" @click="setLang('cn')">简体版</span>
        <span :class="['btn_language', { on: lang === 'tw' }]" @click="setLang('tw')">繁體版</span>
        <span :class="['btn_language', { on: lang === 'en' }]" @click="setLang('en')">ENGLISH</span>
      </div>


      <!-- Login Form -->
      <div class="box_login">
        <label id="usr_lab" :class="usrLabClass">
          <input id="usr" class="userid" type="text" autocomplete="off" required
                 v-model="username" @input="onInput" @focus="onFocus('usr')" @blur="onBlur('usr')">
          <span class="text_input" :data-tooltip="t('usr_tip')"></span>
          <i id="usr_dele" class="btn_clear" @click="clearField('username','usr_lab')">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="m8 7.2 6-6c.2-.2.6-.2.8 0s.2.6 0 .8l-6 6 6 6c.2.2.2.6 0 .8s-.6.2-.8 0l-6-6-6 6c-.2.2-.6.2-.8 0s-.2-.6 0-.8l6-6-6-6c-.2-.2-.2-.6 0-.8s.6-.2.8 0l6 6z" fill-rule="evenodd" clip-rule="evenodd" fill-opacity=".4"/></svg>
          </i>
        </label>

        <label id="pwd_lab" :class="pwdLabClass">
          <input id="pwd" type="password" autocomplete="off" required
                 v-model="password" @input="onInput" @focus="onFocus('pwd')" @blur="onBlur('pwd')"
                 @keyup.enter="doLogin">
          <span class="text_input" :data-tooltip="t('pwd_tip')"></span>
          <i id="pwd_dele" class="btn_clear" @click="clearField('password','pwd_lab')">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="m8 7.2 6-6c.2-.2.6-.2.8 0s.2.6 0 .8l-6 6 6 6c.2.2.2.6 0 .8s-.6.2-.8 0l-6-6-6 6c-.2.2-.6.2-.8 0s-.2-.6 0-.8l6-6-6-6c-.2-.2-.2-.6 0-.8s.6-.2.8 0l6 6z" fill-rule="evenodd" clip-rule="evenodd" fill-opacity=".4"/></svg>
          </i>
        </label>

        <span id="text_error" class="text_error" :style="{ display: error ? 'block' : 'none' }">{{ error }}</span>

        <input id="btn_login" class="btn_login" type="button" :value="loading ? '登入中...' : t('login')"
               :disabled="loading" @click="doLogin">

        <div class="box_remember">
          <label class="check_remember lab_radio">
            <input id="remember" type="checkbox" v-model="remember">
            <span class="checkmark">
              <svg class="check_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18"><path d="M9 0c5 0 9 4 9 9s-4 9-9 9-9-4-9-9 4-9 9-9zm2.8 6.5-3.6 3.9-1.5-1.5a1 1 0 0 0-1.4 0 1 1 0 0 0 0 1.4l2.1 2.4c.2.2.4.3.7.3.3 0 .5-.1.7-.3L13.1 8c.4-.4.4-1 0-1.4-.3-.5-1-.5-1.3-.1z" fill="#33997a"/></svg>
            </span>
            <tt>{{ t('remember') }}</tt>
          </label>
          <span id="btn_forgot" class="btn_forgot">{{ t('forgot') }}</span>
        </div>

        <input id="btn_pwd4" class="btn_passcode" type="button" :value="t('passcode')" style="display:none">
        <input id="btn_oldsite" class="btn_oldsite" type="button" value="旧站入口" style="display:none">
      </div>

      <!-- IP Image Box -->
      <div :class="['box_img', lang.toUpperCase() === 'EN' ? 'EN' : lang.toUpperCase() === 'TW' ? 'TW' : 'CN']">
        <div class="img_festival"></div>
        <div class="img_ip">
          <a id="ip_run" :href="ipUrl" target="_blank">
            <span id="run_ip">hga999.xyz</span>
          </a>
          <div id="ip_guide" class="btn_ipguide"></div>
        </div>
      </div>

      <!-- Browser Recommendations -->
      <div class="box_browser">
        <span>{{ t('browser_title') }}</span>
        <div class="wrap_browser">
          <div class="btn_browser" @click="openUrl('https://www.google.com/chrome')">
            <i><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56"><circle cx="28" cy="28" r="28" fill="#fff"/><circle cx="27.1" cy="27.2" r="19.4" fill="#f2f2f2"/><path d="m55.7 28-.1-2.5-12-12L12.1 42.3l13.3 13.3 2.5.1A27.8 27.8 0 0 0 55.7 28z" fill="#f2f2f2"/><path d="m17.3 25.2-6.2-10.7a21.5 21.5 0 0 1 35.3 2.4H27.9c-5.1.1-9.4 3.6-10.6 8.3z" fill-rule="evenodd" clip-rule="evenodd" fill="#b7aea9"/><path d="M35.7 20.1h12.3A21.5 21.5 0 0 1 28.2 49.5L37 34.2c1.2-1.8 2-3.9 2-6.3 0-3-1.3-5.8-3.3-7.8z" fill-rule="evenodd" clip-rule="evenodd" fill="#c5bfba"/><circle cx="28" cy="28" r="7.8" fill="#c5bfba"/><path d="M30.9 38.6 24.7 49.2A21.5 21.5 0 0 1 9.3 17.5l8.8 15.2c1.8 3.7 5.6 6.3 10 6.3.9 0 1.9-.2 2.8-.4z" fill-rule="evenodd" clip-rule="evenodd" fill="#a59a93"/></svg></i>
            <span>Chrome</span>
          </div>
          <div class="btn_browser" @click="openUrl('https://support.apple.com/downloads/safari')">
            <i><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56"><circle cx="28" cy="28" r="28" fill="#fff"/><path d="M55.7 28c0-.9 0-1.7-.1-2.5l-12-12L12.1 42.4l13.3 13.3c.8.1 1.7.1 2.5.1 15.4 0 27.8-12.4 27.8-27.8z" fill="#f2f2f2"/><circle cx="28" cy="28" r="21.4" fill="#d7d7d7"/><path d="M28 6.5v42.7c11.8 0 21.4-9.6 21.4-21.4C49.3 16.1 39.7 6.5 28 6.5z" fill="#e0e0e0"/><circle cx="28" cy="28" r="19" fill="#a59a93"/><path d="M28 8.9v37.9c10.5 0 19-8.5 19-19-.1-10.4-8.6-18.9-19-18.9z" fill="#b7aea9"/><path d="M26.9 9.8h2.2v3.3h-2.2zM26.9 42.7h2.2V46h-2.2zM42.7 26.9H46v2.2h-3.3zM9.8 26.9h3.3v2.2H9.8z" fill="#fff"/><path d="m25.8 25.8 14.8-10.5-10.5 14.8L15 40.6l10.8-14.8z" fill="#c3c3c3"/><path d="m40.6 15.3-12.7 9v7.5l2.1-1.5 10.6-15z" fill="#e0e0e0"/><path d="m25.8 25.8 14.8-10.5-10.4 14.9-4.4-4.4z" fill="#fff"/></svg></i>
            <span>Safari</span>
          </div>
          <div class="btn_browser" @click="openUrl('https://www.mozilla.org')">
            <i><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56"><ellipse cx="28" cy="27.9" rx="28" ry="27.9" fill="#fff"/><path d="M56 27.9c0-.2 0-.5 0-.7L41.5 12.8 25.7 25.3 11.8 11.5l-.7 1.8 2.6 28.9 13.8 13.8c.2 0 .3 0 .5 0C43.5 55.9 56 43.4 56 27.9z" fill="#f2f2f2"/><ellipse cx="27.7" cy="27.5" rx="20.2" ry="20.2" fill="#faf3ee"/><path d="M47.9 27.5c0-11.1-8.9-20-20-20.2v40.4C39 47.6 47.9 38.6 47.9 27.5z" fill="#e7dfd9"/><path d="m22 34.8s2.6 3.5 8.2 3.5c5.6 0 8.8-4.2 8.8-8.3" fill="none" stroke="#da5f27" stroke-width="1.5"/><path d="M47.9 27.5c0-4.8-1.7-9.2-4.5-12.7s-8.3-4.8-8.3-4.8c4.5 2.5 6 6.4 6 6.4-1.6-1.9-3.8-2.2-3.8-2.2 4.4 3.5 4.3 11.2 4.3 11.2-.4-1.7-1.9-2.8-1.9-2.8.9 4.6-.2 8.6-.2 8.6 0-.7-.6-1.3-.6-1.3 0 4.1-3.2 8.3-8.8 8.3-5.6 0-8.2-3.5-8.2-3.5 0 0-1.1-.8-1.9-.5-.7.3-1.9 2.7.8 4.1 0 0 3.8 1.3 7.5.9 3.6-.4 3.4 2.7 1.5 3-3.6.3-9.9 1.1-9.9 1.1z" fill="#ad6c3e"/></svg></i>
            <span>{{ t('browser_fox') }}</span>
          </div>
        </div>
        <p>{{ t('browser_text1') }}<a id="systemreq" href="#" @click.prevent>{{ t('browser_req') }}</a>{{ t('browser_text2') }}</p>
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
const remember = ref(false)
const loading = ref(false)
const error = ref('')
const lang = ref('cn')

const labels = {
  cn: { usr_tip: '登入帐号', pwd_tip: '密码', login: '登入', remember: '记住我的帐号', forgot: '忘记密码?', passcode: '用简易密码登入', browser_title: '我们推荐使用以下浏览器以获得最佳使用体验:', browser_fox: '火狐', browser_text1: '如果您在使用本网站遇到任何问题，请查看我们列出的浏览器和系统的', browser_req: '最低需求', browser_text2: '。', ip_url: 'http://hga999.xyz/' },
  tw: { usr_tip: '登入帳號', pwd_tip: '密碼', login: '登入', remember: '記住我的帳號', forgot: '忘記密碼?', passcode: '用簡易密碼登入', browser_title: '我們推薦使用以下瀏覽器以獲得最佳使用體驗:', browser_fox: '火狐', browser_text1: '如果您在使用本網站遇到任何問題，請查看我們列出的瀏覽器和系統的', browser_req: '最低需求', browser_text2: '。', ip_url: 'http://hga999.xyz/' },
  en: { usr_tip: 'Username', pwd_tip: 'Password', login: 'LOGIN', remember: 'Remember Me', forgot: 'Forgot Password?', passcode: 'Login with Simple Password', browser_title: 'We recommend the following browsers for the best experience:', browser_fox: 'Firefox', browser_text1: 'If you are experiencing issues, please check our listed browsers and system ', browser_req: 'minimum requirements', browser_text2: '.', ip_url: 'https://hga999.xyz/' }
}

function t(key) { return labels[lang.value]?.[key] || key }
const ipUrl = computed(() => labels[lang.value]?.ip_url || 'http://hga999.xyz/')

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

function setLang(l) { lang.value = l }
function onFocus(field) { if (field === 'usr') usrFocused.value = true; else pwdFocused.value = true }
function onBlur(field) { if (field === 'usr') { usrFocused.value = false; usrTouched.value = true } else { pwdFocused.value = false; pwdTouched.value = true } }
function onInput() { error.value = '' }
function clearField(field, labId) {
  if (field === 'username') { username.value = ''; usrFocused.value = false }
  else { password.value = ''; pwdFocused.value = false }
  error.value = ''
}
function openUrl(url) { window.open(url, '_blank') }

async function doLogin() {
  error.value = ''
  usrTouched.value = true
  pwdTouched.value = true

  if (!username.value || !password.value) {
    error.value = !username.value ? '请输入您的登入帐号' : '请输入密码'
    return
  }

  loading.value = true
  try {
    await store.loginUser(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.error || '登入失败，请稍后再试'
  } finally {
    loading.value = false
  }
}
</script>

<style>
/* ===== Login Page (exact hga039 replica) ===== */
.login { background: #f5f5f5; }
.bg_login {
  width: 100%; min-height: 100%; padding-bottom: 16px;
  background: #f5f5f5; flex: none; min-height: 100dvh;
}

.box_language {
  width: 100%; height: 56px; line-height: 56px; text-align: center;
  font-size: 14px; background: #503f32;
}
.btn_language {
  display: inline-block; width: 33.33%; height: 100%; max-width: 107px;
  margin-right: -4px; cursor: pointer; color: rgba(255,255,255,0.72);
  transition: all 0.3s ease; user-select: none;
}
.btn_language.on { color: #debb69; }

.icon_login { display: block; width: 55px; height: 55px; margin: 16px auto; border-radius: 50%; overflow: hidden; }
.icon_login svg { display: block; width: 100%; height: 100%; }

.box_login {
  width: 100%; max-width: 320px; margin: 16px auto; padding: 24px 16px 16px;
  text-align: center; background: #fff;
}

.lab_input { position: relative; display: block; width: 100%; height: 48px; margin-bottom: 16px; }
.lab_input > input {
  display: block; width: 100%; height: 100%; margin: 0; padding: 0 32px 0 16px;
  font-size: 16px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.32);
  color: #000; box-shadow: none; transition: all 0.3s ease;
  pointer-events: auto; background: #fff; outline: none;
}
input.userid { font-family: 'Tahoma','Verdana',serif; }
input[type="text"] { transform: translate3d(0,0,0); }
input[type="button"] { cursor: pointer; }

.text_input { line-height: normal !important; pointer-events: none; }
.text_input::after {
  content: attr(data-tooltip); position: absolute; top: 0; left: 14px;
  display: flex; height: 100%; align-items: center; padding: 0 4px;
  font-size: 16px; color: rgba(0,0,0,0.24); background: #fff0;
  transition: all 0.3s ease, background 0.1s 0.1s;
}
.lab_input > input:valid ~ .text_input::after {
  top: -8px; height: 16px; font-size: 12px; color: rgba(0,0,0,0.56); background: #fff;
}
.lab_input.on > input { border: 2px solid #19805c; }
.lab_input.on .text_input::after {
  top: -8px; height: 16px; font-size: 12px; color: #19805c !important; background: #fff;
}
.lab_input.error > input { border: 2px solid #e76565 !important; }
.lab_input.error.on > input { border: 2px solid #e76565 !important; }
.lab_input.error .text_input::after,
.lab_input.on.error .text_input::after { color: #e76565 !important; }

.lab_input .btn_clear {
  position: absolute; top: 8px; right: 8px; width: 32px; height: 32px; padding: 8px;
  transition: none !important; pointer-events: auto; z-index: -1; cursor: default;
}
.lab_input .btn_clear svg {
  width: 100%; height: 100%; opacity: 0; fill: rgba(0,0,0,0.4); pointer-events: none;
}
.lab_input.on > input:valid ~ .btn_clear { z-index: 1; cursor: pointer; }
.lab_input .btn_clear:active { z-index: 1; }

.text_error {
  display: none; width: 100%; line-height: 16px; margin-bottom: 16px;
  text-align: center; font-size: 12px; color: #ce3636;
}

.btn_login {
  width: 100%; height: 48px; line-height: 48px; margin-bottom: 16px;
  padding: 0 16px; border-radius: 4px; text-align: center; font-size: 12px;
  font-weight: bold; border: none; color: #fff; background: #19805c;
  transition: background 0.3s ease;
}
.btn_login:disabled { opacity: 0.6; cursor: not-allowed; }
.btn_passcode {
  width: 100%; height: 48px; line-height: 48px; margin-bottom: 16px;
  padding: 0 16px; border-radius: 4px; font-size: 12px; font-weight: 600;
  border: none; color: #fff; background: #9b8d79; transition: background 0.3s ease;
}
.btn_oldsite {
  width: 100%; height: 48px; line-height: 48px; padding: 0 16px;
  border-radius: 4px; font-size: 14px; border: none; color: #007ba8;
  background: #fff; transition: background 0.3s ease;
}

.box_remember { width: 100%; height: 48px; line-height: 48px; margin-bottom: 11px; text-align: left; }
.lab_radio {
  position: relative; float: left; display: block;
  color: rgba(0,0,0,0.64); user-select: none;
}
.check_remember { height: 48px; margin-right: 8px; }
.lab_radio input { position: absolute; opacity: 0; cursor: pointer; height: 0; width: 0; }
.checkmark {
  display: inline-block; width: 18px; height: 18px; margin: 3px;
  vertical-align: middle; border-radius: 50%; border: 1px solid rgba(0,0,0,0.64);
}
.lab_radio tt {
  display: inline-block; margin-left: 4px; vertical-align: middle;
  font-size: 14px; color: rgba(0,0,0,0.64);
}
.lab_radio input:checked ~ .checkmark { border: none !important; }
.check_svg { display: none; width: 18px; height: 18px; }
.lab_radio input:checked ~ .checkmark .check_svg { display: block; }

.btn_forgot {
  float: right; display: block; margin-top: 1px; text-align: right;
  font-size: 14px; color: #0066CC; cursor: pointer;
}

.box_img { display: block; width: 100%; max-width: 320px; margin: 16px auto 0; }
.img_festival { display: none; }
.img_ip {
  position: relative; display: flex; width: 100%; height: 156px;
  background-size: contain; background-position: center; background-repeat: no-repeat;
    background-image: url(data:image/png;base64,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);
}
.img_ip a { width: 172px; }
.img_ip .btn_ipguide { width: auto; height: 100%; flex: 1 1 auto; cursor: pointer; }
.img_ip span {
  position: absolute; display: inline-flex; height: 32px; font-size: 20px;
  line-height: 24px; font-weight: bold; color: #0499C8; align-items: center;
}
.CN .img_ip span, .TW .img_ip span { top: 90px; left: 16px; }
.EN .img_ip span { top: 97px; left: 16px; }

.box_browser {
  display: flex; width: 100%; max-width: 320px; margin: 16px auto; padding: 16px;
  line-height: 16px; font-size: 14px; flex-direction: column; align-content: center;
  flex: none; color: #000; background: #fff;
}
.box_browser > span { width: 100%; font-weight: bold; }
.box_browser a { display: inline-block; color: #0066CC; cursor: pointer; }
.box_browser p { margin-top: 4px; }
.wrap_browser {
  display: flex; width: 100%; margin: 16px 0; align-items: center; justify-content: center;
}
.btn_browser {
  display: flex; width: 64px; height: 84px; margin-right: 8px; line-height: 16px;
  font-size: 12px; flex-direction: column; align-items: center; justify-content: center;
  border-radius: 8px; color: #000; cursor: pointer; user-select: none;
}
.btn_browser:last-child { margin-right: 0; }
.btn_browser span { font-size: 12px; }
.btn_browser i { width: 56px; height: 56px; margin-bottom: 4px; border-radius: 50%; }
.btn_browser i svg { width: 100%; height: 100%; }

/* Desktop: center the mobile layout */
@media (min-width: 641px) {
  .bg_login {
    justify-content: flex-start;
    padding-top: 20px;
  }
}
</style>
