<template>
  <div class="hero-wrap">
    <div class="hero-badge"><el-icon><HomeFilled /></el-icon><span>RAG 智能问答</span></div>
    <h1 class="hero-title">把问题变成<span class="hero-highlight">清晰答案</span></h1>
    <p class="hero-sub">结构化提问、知识检索与深度思考，一次对话给出可执行方案</p>

    <QuestionInput
      :question="question"
      :deepThink="deepThink"
      :isLoading="isLoading"
      :inputPlaceholder="inputPlaceholder"
      @send="$emit('send')"
      @update:question="$emit('update:question', $event)"
      @update:deepThink="$emit('update:deepThink', $event)"
    />

    <div v-if="deepThink" class="deep-think-tip"><el-icon><Opportunity /></el-icon><span>深度思考模式已开启</span></div>
    <div class="input-hint"><kbd>Enter</kbd><span>发送</span><span class="dot">·</span><kbd>Shift + Enter</kbd><span>换行</span></div>

    <div class="divider-row"><span class="divider-line"></span><span class="divider-text">试试这些开场</span><span class="divider-line"></span></div>

    <div class="starter-cards">
      <div v-for="card in starterCards" :key="card.title" class="starter-card" @click="$emit('fillInput', card.hint)">
        <div class="starter-card-top">
          <div class="starter-icon" :style="{ background: card.iconBg, color: card.iconColor }"><el-icon><component :is="card.icon" /></el-icon></div>
          <el-icon class="starter-arrow"><TopRight /></el-icon>
        </div>
        <div class="starter-title">{{ card.title }}</div>
        <div class="starter-sub">{{ card.subtitle }}</div>
        <div class="starter-hint">{{ card.hintLabel }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { HomeFilled, Opportunity, TopRight, Notebook, CircleCheck } from '@element-plus/icons-vue'
import QuestionInput from './QuestionInput.vue'

defineProps({
  question: String,
  deepThink: Boolean,
  isLoading: Boolean,
  inputPlaceholder: String,
})

defineEmits(['send', 'fillInput', 'update:question', 'update:deepThink'])

const starterCards = [
  { icon: Notebook, iconBg: '#eef2ff', iconColor: '#6366f1', title: '实时数据', subtitle: '销售汇总数据统计', hintLabel: '推荐问法：销售数据统计...', hint: '销售数据统计，如：销售总额、销售趋势' },
  { icon: CircleCheck, iconBg: '#e8f6ef', iconColor: '#22a06b', title: '业务系统', subtitle: '数据安全', hintLabel: '推荐问法：数据权限、访问控制...', hint: '数据权限、访问控制、安全策略' },
  { icon: Opportunity, iconBg: '#fef6e7', iconColor: '#e0a020', title: '系统交互', subtitle: '关于助手', hintLabel: '推荐问法：询问助手是做什么的...', hint: '询问助手是做什么的、是谁、能做什么等' }
]
</script>

<style scoped>
.hero-wrap { width: 100%; max-width: 820px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; padding-top: 60px; overflow-y: auto; }
.hero-badge { display: flex; align-items: center; gap: 6px; background: #ffffff; border: 1px solid #eef0f4; color: #606773; font-size: 12.5px; padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 26px; }
.hero-badge .el-icon { color: #4f7fff; }
.hero-title { font-size: 46px; font-weight: 700; color: #1d2129; text-align: center; margin: 0 0 16px 0; line-height: 1.3; }
.hero-highlight { color: #4f7fff; }
.hero-sub { font-size: 16px; color: #6b7280; text-align: center; margin: 0 0 36px 0; }
.deep-think-tip { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #4f7fff; margin-top: 12px; width: 100%; }
.input-hint { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #b0b8c4; margin: 12px 0 34px 0; }
.input-hint .dot { color: #d5dae2; }
.input-hint kbd { background: #f0f1f5; border-radius: 4px; padding: 2px 7px; font-family: inherit; font-size: 11px; color: #606773; }
.divider-row { display: flex; align-items: center; gap: 14px; width: 100%; max-width: 340px; margin-bottom: 26px; }
.divider-line { flex: 1; height: 1px; background: #e5e8ef; }
.divider-text { font-size: 12.5px; color: #9aa3b2; white-space: nowrap; }
.starter-cards { display: flex; gap: 20px; width: 100%; flex-wrap: wrap; margin-bottom: 20px; }
.starter-card { flex: 1; min-width: 220px; background: #ffffff; border-radius: 14px; padding: 18px 18px 16px 18px; box-shadow: 0 2px 12px rgba(0,0,0,0.04); cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.starter-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
.starter-card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.starter-icon { width: 32px; height: 32px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
.starter-arrow { color: #c2c8d1; font-size: 14px; }
.starter-title { font-size: 15px; font-weight: 600; color: #1d2129; margin-bottom: 4px; }
.starter-sub { font-size: 13px; color: #86909c; margin-bottom: 10px; }
.starter-hint { font-size: 12px; color: #b0b8c4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>