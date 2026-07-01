<template>
  <div>
    <!-- IN-PLAY Events -->
    <div class="home_live" v-if="liveSports.length">
      <div class="title_game"><tt>滚球中赛事</tt></div>
      <div class="home_live_scroll">
        <div class="live_sport">
          <div v-for="s in liveSports" :key="s.sport" class="btn_live_sport" @click="openSport(s.sport, 'live')">
            <tt>{{ s.count }}</tt>
            <i class="icon_sport">{{ sportIcon(s.sport) }}</i>
            <span>{{ sportName(s.sport) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- SPORTS Section -->
    <div class="title_game" style="margin-top:4px;"><tt>体育</tt></div>
    <div class="wrap_sport">
      <div v-for="card in sportCards" :key="card.key" class="box_sport" :class="card.key">
        <div class="title_sport"><span>{{ card.name }}</span></div>
        <div class="pic_sport">
          <div style="font-size:48px;opacity:0.3;">{{ sportIcon(card.key) }}</div>
        </div>
        <div class="box_sport_btn">
          <div class="btn_sport_new" @click="openSport(card.key, 'live')" v-if="card.live !== undefined">
            <span>滚球</span>
            <p class="num_sport_game"><tt>{{ card.live }}</tt><i>→</i></p>
          </div>
          <div class="btn_sport_new" @click="openSport(card.key, 'today')" v-if="card.today !== undefined">
            <span>今日</span>
            <p class="num_sport_game"><tt>{{ card.today }}</tt><i>→</i></p>
          </div>
          <div class="btn_sport_new" @click="openSport(card.key, 'early')" v-if="card.early !== undefined">
            <span>早盘</span>
            <p class="num_sport_game"><tt>{{ card.early }}</tt><i>→</i></p>
          </div>
        </div>
      </div>
    </div>

    <!-- Other sports (建设中) -->
    <div class="title_game"><tt>其他运动</tt></div>
    <div class="wrap_sport">
      <div v-for="s in otherSports" :key="s.key" class="box_sport" style="opacity:0.5;">
        <div class="title_sport"><span>{{ s.name }}</span></div>
        <div class="pic_sport"><div style="font-size:48px;">🏗️</div></div>
        <div class="box_sport_btn" style="justify-content:center;padding:16px;">
          <span style="color:#999;">正在建设中</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()

const liveSports = ref([])
const sportCards = ref([])

const otherSports = [
  { key: 'VB', name: '排球' }, { key: 'BM', name: '羽毛球' }, { key: 'TT', name: '乒乓球' },
  { key: 'BS', name: '棒球' }, { key: 'SK', name: '斯诺克' }, { key: 'OP', name: '其他' },
]

function sportName(key) {
  const map = { FT:'足球', BK:'篮球 & 美式足球', TN:'网球', ES:'eSports', VB:'排球', BM:'羽毛球', TT:'乒乓球', BS:'棒球', SK:'斯诺克', OP:'其他' }
  return map[key] || key
}

function sportIcon(key) {
  const map = { FT:'⚽', BK:'🏀', TN:'🎾', ES:'🎮', VB:'🏐', BM:'🏸', TT:'🏓', BS:'⚾', SK:'🎱', OP:'🏅' }
  return map[key] || '🏅'
}

function openSport(sport, period) {
  router.push(`/sport/${sport}/${period}`)
}

onMounted(async () => {
  try {
    const data = await store.fetchHomeData()
    liveSports.value = data.liveSports || []
    sportCards.value = data.sportCards || []
  } catch(e) {
    // Fallback: show static data
    sportCards.value = [
      { key:'FT', name:'足球', live:0, today:0, early:0 },
      { key:'BK', name:'篮球 & 美式足球', live:0, today:0, early:0 },
      { key:'TN', name:'网球', live:0, today:0, early:0 },
    ]
  }
})
</script>
