<template>
  <div>
    <router-link to="/" class="back-link">← 返回</router-link>
    <div v-if="!match && store.loading" class="empty-state"><div class="empty-state-icon">⏳</div><div>加载中...</div></div>
    <template v-if="match">
      <div class="card" style="margin-top:6px;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#FAFAFA;border-bottom:1px solid var(--border-light);font-size:10px;color:var(--text-muted);"><span>{{ match.league_name }}</span><span :class="'tag '+(match.status==='live'?'tag-red':match.status==='pending'?'tag-orange':'tag-green')">{{ store.getMatchStatusText(match.status) }}</span></div>
        <div style="padding:14px 12px;"><div class="match-teams-row"><div class="match-team-col"><div class="match-team-name">{{ match.home_team }}</div></div><div class="match-vs-area"><div v-if="match.status==='pending'" class="match-time-text">{{ store.formatMatchTime(match.match_date) }}</div><div v-else class="match-score-display">{{ match.scores_home }} - {{ match.scores_away }}</div></div><div class="match-team-col"><div class="match-team-name">{{ match.away_team }}</div></div></div></div>
      </div>
      <div v-if="match.status==='pending' && odds" class="card">
        <div style="padding:12px;">
          <div class="market-tabs"><button v-for="mt in marketTypes" :key="mt.key" class="market-tab" :class="{active:activeMarket===mt.key}" @click="activeMarket=mt.key;selectedOption=''">{{ mt.label }}</button></div>
          <div v-if="activeMarket==='ML'" class="bet-grid bet-grid-3">
            <div class="bet-option" :class="{selected:sel==='home'}" @click="sel='home'"><span class="bet-option-label">主胜</span><span class="bet-option-odds">{{ odds.ML?.data?.home }}</span></div>
            <div class="bet-option" :class="{selected:sel==='draw'}" @click="sel='draw'"><span class="bet-option-label">平局</span><span class="bet-option-odds">{{ odds.ML?.data?.draw }}</span></div>
            <div class="bet-option" :class="{selected:sel==='away'}" @click="sel='away'"><span class="bet-option-label">客胜</span><span class="bet-option-odds">{{ odds.ML?.data?.away }}</span></div>
          </div>
          <div v-if="activeMarket==='Spread'" class="bet-grid">
            <div class="bet-option" :class="{selected:sel==='home'}" @click="sel='home'"><span class="bet-option-label">主队赢盘</span><span class="bet-option-hdp">{{ spreadHdp }}</span><span class="bet-option-odds">{{ odds.Spread?.data?.home }}</span></div>
            <div class="bet-option" :class="{selected:sel==='away'}" @click="sel='away'"><span class="bet-option-label">客队赢盘</span><span class="bet-option-hdp">{{ spreadHdp }}</span><span class="bet-option-odds">{{ odds.Spread?.data?.away }}</span></div>
          </div>
          <div v-if="activeMarket==='Totals'" class="bet-grid">
            <div class="bet-option" :class="{selected:sel==='over'}" @click="sel='over'"><span class="bet-option-label">大 {{ odds.Totals?.data?.hdp }}</span><span class="bet-option-odds">{{ odds.Totals?.data?.over }}</span></div>
            <div class="bet-option" :class="{selected:sel==='under'}" @click="sel='under'"><span class="bet-option-label">小 {{ odds.Totals?.data?.hdp }}</span><span class="bet-option-odds">{{ odds.Totals?.data?.under }}</span></div>
          </div>
          <div v-if="activeMarket==='CS'" class="bet-grid">
            <div v-for="s in (odds.CS?.data?.scores||[])" :key="s.label" class="bet-option" :class="{selected:sel===s.label}" @click="sel=s.label"><span class="bet-option-label">{{ s.label }}</span><span class="bet-option-odds">@{{ s.odds }}</span></div>
          </div>
          <div v-if="sel" style="margin-top:10px;">
            <div class="bet-input-row"><input v-model.number="betAmount" type="number" class="input" placeholder="金币数（最低50）" /><button class="btn btn-accent btn-wide" :disabled="betting" @click="doBet">{{ betting?'下注中...':'确认下注' }}</button></div>
            <div v-if="betAmount>=50&&currOdds>0" class="bet-summary" style="margin-top:10px;"><div class="bet-summary-text">预估奖励</div><div class="bet-summary-amount">{{ Math.round(betAmount*currOdds) }} 金币</div><div class="bet-summary-odds">赔率 @{{ currOdds }}</div></div>
            <div v-if="betError" style="color:var(--red);font-size:12px;text-align:center;margin-top:6px;">{{ betError }}</div>
          </div>
          <div v-if="!sel" style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">请选择投注选项</div>
        </div>
      </div>
      <div v-if="match.status==='live'" class="card"><div style="text-align:center;padding:20px;color:var(--text-muted);">比赛进行中，V2.0 支持滚球下注</div></div>
      <div v-if="match.status==='settled'" class="card"><div style="text-align:center;padding:20px;color:var(--text-muted);">比赛已结束</div></div>
    </template>
  </div>
</template>
<script setup>
import { ref, computed, inject, onMounted } from 'vue'; import { useRoute } from 'vue-router'; import { useAppStore } from '../stores/app'
const store = useAppStore(); const route = useRoute(); const showToast = inject('showToast')
const activeMarket = ref('ML'); const sel = ref(''); const betAmount = ref(100); const betting = ref(false); const betError = ref('')
const marketTypes = [{key:'ML',label:'胜平负'},{key:'Spread',label:'让球盘'},{key:'Totals',label:'大小球'},{key:'CS',label:'波胆'}]
const match = computed(() => store.getMatchById(route.params.id))
const odds = computed(() => store.getOdds(route.params.id))
const spreadHdp = computed(()=>{if(!odds.value?.Spread?.data)return'';const h=odds.value.Spread.data.hdp;return h>0?`主队让${h}球`:h<0?`主队受让${-h}球`:'平手盘'})
const currOdds = computed(()=>{if(!odds.value||!sel.value)return 0;const o=odds.value;const mk=activeMarket.value;if(mk==='ML')return o.ML?.data?.[sel.value]||0;if(mk==='Spread')return o.Spread?.data?.[sel.value]||0;if(mk==='Totals')return o.Totals?.data?.[sel.value]||0;if(mk==='CS'){const s=(o.CS?.data?.scores||[]).find(x=>x.label===sel.value);return s?.odds||0}return 0})
async function doBet(){if(!sel.value)return;betting.value=true;betError.value='';try{const r=await store.placeBet(match.value.id,activeMarket.value,sel.value,betAmount.value);if(r.success){showToast(`下注成功！预估 ${r.bet.potential_win} 金币`);sel.value='';betAmount.value=100}}catch(e){betError.value=e.response?.data?.error||'下注失败'}finally{betting.value=false}}
onMounted(async()=>{await store.fetchMatchDetail(route.params.id)})
</script>