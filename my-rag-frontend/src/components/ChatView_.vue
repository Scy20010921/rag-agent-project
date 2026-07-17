<template>
  <div class="chat-wrap">
    <div class="message-list" ref="messageListRef">
      <template v-for="msg in messages" :key="msg.id || msg.created_at">
        <!-- 状态提示（"正在思考..."、"正在调用工具..."） -->
        <div v-if="msg.role === 'status'" class="status-row">
          <div class="status-text">{{ msg.text }}</div>
        </div>
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="user-bubble-row"><div class="user-bubble">{{ msg.content }}</div></div>
        <!-- 工具调用卡片 -->
        <div v-else-if="msg.role === 'tool'" class="tool-card-row">
          <div class="tool-card" :class="{ 'tool-running': msg.status === 'running', 'tool-done': msg.status === 'done' }">
            <div class="tool-card-header">
              <el-icon class="tool-icon"><Tools /></el-icon>
              <span class="tool-name">{{ msg.toolName }}</span>
              <span v-if="msg.status === 'running'" class="tool-spinner"></span>
              <span v-else class="tool-check">✓</span>
            </div>
            <div class="tool-input" v-if="msg.input">输入: {{ msg.input }}</div>
            <div class="tool-output" v-if="msg.output">{{ msg.output }}</div>
          </div>
        </div>
        <!-- AI 回复 -->
        <div v-else class="assistant-row">
          <div v-if="!msg.content && isLoading && msg === currentAssistantMsg" class="assistant-thinking"><span class="think-jump"></span><span class="think-jump"></span><span class="think-jump"></span></div>
          <div v-else class="assistant-text markdown-body" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </template>
    </div>

    <div class="chat-input-bar">
      <QuestionInput
        :question="question"
        :deepThink="deepThink"
        :isLoading="isLoading"
        :inputPlaceholder="inputPlaceholder"
        @send="$emit('send')"
        @stop="$emit('stop')"
        @update:question="$emit('update:question', $event)"
        @update:deepThink="$emit('update:deepThink', $event)"
      />
      <div v-if="deepThink" class="deep-think-tip"><el-icon><Opportunity /></el-icon><span>深度思考模式已开启</span></div>
      <div class="input-hint"><kbd>Enter</kbd><span>发送</span><span class="dot">·</span><kbd>Shift + Enter</kbd><span>换行</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Tools, Opportunity } from '@element-plus/icons-vue'
import QuestionInput from './QuestionInput.vue'
import { renderMarkdown } from '../utils/markdown.js'

defineProps({
  question: String,
  deepThink: Boolean,
  isLoading: Boolean,
  inputPlaceholder: String,
  messages: { type: Array, default: () => [] },
  currentAssistantMsg: Object,
})

const messageListRef = ref(null)
defineExpose({ messageListRef })
defineEmits(['send', 'stop', 'update:question', 'update:deepThink'])
</script>

<style scoped>
.status-row { display: flex; justify-content: flex-start; }
.status-text { font-size: 13px; color: #94a3b8; padding: 2px 4px; font-style: italic; }
.chat-wrap { flex: 1; display: flex; flex-direction: column; width: 100%; max-width: 900px; margin: 0 auto; min-height: 0; }
.message-list { flex: 1; overflow-y: auto; padding: 10px 4px 20px 4px; display: flex; flex-direction: column; gap: 18px; scrollbar-width: thin; scrollbar-color: #d5dae2 transparent; }
.message-list::-webkit-scrollbar { width: 6px; }
.message-list::-webkit-scrollbar-track { background: transparent; }
.message-list::-webkit-scrollbar-thumb { background: #d5dae2; border-radius: 3px; }
.chat-input-bar { flex-shrink: 0; padding-top: 8px; padding-bottom: 4px; background: linear-gradient(to top, #f2f4fa 60%, rgba(242,244,250,0)); }
.user-bubble-row { display: flex; justify-content: flex-end; }
.user-bubble { max-width: 70%; background: #d8e6ff; color: black; font-size: 14.5px; line-height: 1.6; padding: 10px 16px; border-radius: 16px 16px 4px 16px; white-space: pre-wrap; word-break: break-word; }
.assistant-row { display: flex; justify-content: flex-start; }
.assistant-text { max-width: 80%; font-size: 14.5px; line-height: 1.7; color: #1d2129; white-space: normal; word-break: break-word; }
.assistant-text :deep(p) { margin: 0 0 10px 0; }
.assistant-text :deep(p:last-child) { margin-bottom: 0; }
.assistant-text :deep(code) { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 13px; font-family: 'Menlo', 'Monaco', monospace; }
.assistant-text :deep(pre) { background: #f5f9ff; color: #e2e8f0; border-radius: 8px; padding: 14px 16px; overflow-x: auto; margin: 10px 0; }
.assistant-text :deep(pre code) { background: none; padding: 0; font-size: 13px; }
.assistant-text :deep(ul), .assistant-text :deep(ol) { padding-left: 20px; margin: 10px 0; }
.assistant-text :deep(li) { margin-bottom: 4px; }
.assistant-text :deep(strong) { font-weight: 600; }
.assistant-text :deep(blockquote) { border-left: 3px solid #4f7fff; padding-left: 12px; color: #64748b; margin: 10px 0; }
.assistant-text :deep(table) { border-collapse: collapse; width: 100%; margin: 10px 0; }
.assistant-text :deep(th), .assistant-text :deep(td) { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; font-size: 13px; }
.assistant-text :deep(th) { background: #f8fafc; font-weight: 600; }
.assistant-thinking { display: flex; align-items: center; gap: 5px; padding: 4px 0; }
.think-jump { width: 6px; height: 6px; border-radius: 50%; background: #c2c8d1; animation: think-jump-anim 1.1s infinite ease-in-out; }
.think-jump:nth-child(2) { animation-delay: 0.15s; }
.think-jump:nth-child(3) { animation-delay: 0.3s; }
@keyframes think-jump-anim { 0%,60%,100% { transform: translateY(0); opacity: 0.5; } 30% { transform: translateY(-4px); opacity: 1; } }
.tool-card-row { display: flex; justify-content: flex-start; }
.tool-card { max-width: 85%; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; font-size: 13px; }
.tool-card.tool-running { border-color: #93c5fd; background: #eff6ff; }
.tool-card.tool-done { border-color: #86efac; background: #f0fdf4; }
.tool-card-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.tool-icon { font-size: 15px; color: #6366f1; }
.tool-name { font-weight: 600; font-size: 13px; color: #334155; }
.tool-spinner { width: 12px; height: 12px; border: 2px solid #93c5fd; border-top-color: #3b82f6; border-radius: 50%; animation: tool-spin 0.6s linear infinite; }
.tool-check { color: #22c55e; font-weight: 700; }
.tool-input { color: #64748b; font-size: 12px; margin-top: 3px; }
.tool-output { color: #1e293b; font-size: 12.5px; margin-top: 4px; word-break: break-word; }
@keyframes tool-spin { to { transform: rotate(360deg); } }
.deep-think-tip { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #4f7fff; margin-top: 12px; width: 100%; }
.input-hint { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #b0b8c4; margin: 12px 0 34px 0; }
.input-hint .dot { color: #d5dae2; }
.input-hint kbd { background: #f0f1f5; border-radius: 4px; padding: 2px 7px; font-family: inherit; font-size: 11px; color: #606773; }
</style>