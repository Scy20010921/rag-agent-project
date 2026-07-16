<template>
  <el-container class="app-container">
    <el-aside width="270px" class="sidebar">
      <div class="logo-area">
        <div class="logo-icon"><el-icon><ChatDotRound /></el-icon></div>
        <div class="logo-text">
          <span class="logo-title">RAG 智能问答</span>
          <span class="logo-sub">Powered by AI</span>
        </div>
      </div>
 
      <div class="quick-start-card" v-if="!hasMessages">
        <div class="quick-start-top">
          <span class="quick-start-label">快速开始</span>
          <span class="quick-start-badge">新内容</span>
        </div>
        <div class="new-chat-row" @click="startNewChat">
          <div class="new-chat-icon"><el-icon><Plus /></el-icon></div>
          <div class="new-chat-text">
            <span class="new-chat-title">新建对话</span>
            <span class="new-chat-sub">从空白开始</span>
          </div>
        </div>
      </div>
 
      <!-- 进入对话后显示新对话 + 返回首页按钮 -->
      <div v-else class="quick-start-card">
        <div class="new-chat-row" @click="startNewChat">
          <div class="new-chat-icon"><el-icon><Plus /></el-icon></div>
          <div class="new-chat-text">
            <span class="new-chat-title">新建对话</span>
            <span class="new-chat-sub">从空白开始</span>
          </div>
        </div>
      </div>
 
      <div class="history-section">
        <div class="history-label">历史对话</div>
        <ul class="history-list">
          <li
            v-for="s in sessions"
            :key="s.id"
            class="history-item"
            :class="{ active: s.id === currentSessionId }"
            @click="switchSession(s.id)"
          >
            {{ s.title }}
          </li>
          <li v-if="sessions.length === 0" class="history-item-empty">暂无历史对话</li>
        </ul>
      </div>
 
      <div class="user-info">
        <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a53f6f0f6dpng.png" />
        <span class="user-name">admin</span>
      </div>
    </el-aside>
 
    <el-main class="main-content">
      <div v-if="hasMessages" class="top-bar">
        <div class="top-bar-new-chat" @click="startNewChat">新对话</div>
      </div>
 
      <div v-if="!hasMessages" class="hero-wrap">
        <div class="hero-badge"><el-icon><HomeFilled /></el-icon><span>RAG 智能问答</span></div>
        <h1 class="hero-title">把问题变成<span class="hero-highlight">清晰答案</span></h1>
        <p class="hero-sub">结构化提问、知识检索与深度思考，一次对话给出可执行方案</p>
        <div class="question-card">
          <el-input v-model="question" type="textarea" :rows="2" :placeholder="inputPlaceholder" class="question-input" resize="none" @keydown.enter.prevent="sendQuestion" />
          <div class="question-toolbar">
            <div class="deep-think-toggle" :class="{ on: deepThink }" @click="deepThink = !deepThink">
              <el-icon><MagicStick /></el-icon><span>深度思考</span><span v-if="deepThink" class="think-dot"></span>
            </div>
            <div class="send-btn" :class="{ disabled: !question.trim() || isLoading }" @click="sendQuestion"><el-icon><Promotion /></el-icon></div>
          </div>
        </div>
        <div v-if="deepThink" class="deep-think-tip"><el-icon><Opportunity /></el-icon><span>深度思考模式已开启</span></div>
        <div class="input-hint"><kbd>Enter</kbd><span>发送</span><span class="dot">·</span><kbd>Shift + Enter</kbd><span>换行</span></div>
        <div class="divider-row"><span class="divider-line"></span><span class="divider-text">试试这些开场</span><span class="divider-line"></span></div>
        <div class="starter-cards">
          <div v-for="card in starterCards" :key="card.title" class="starter-card" @click="fillInput(card.hint)">
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
 
      <div v-else class="chat-wrap">
        <div class="message-list" ref="messageListRef">
          <template v-for="msg in messages" :key="msg.id || msg.created_at">
            <div v-if="msg.role === 'user'" class="user-bubble-row"><div class="user-bubble">{{ msg.content }}</div></div>
            <div v-else class="assistant-row">
              <div v-if="!msg.content && isLoading && msg === currentAssistantMsg" class="assistant-thinking"><span class="think-jump"></span><span class="think-jump"></span><span class="think-jump"></span></div>
              <div v-else class="assistant-text">{{ msg.content }}</div>
            </div>
          </template>
        </div>
        <div class="chat-input-bar">
          <div class="question-card">
            <el-input v-model="question" type="textarea" :rows="2" :placeholder="inputPlaceholder" class="question-input" resize="none" @keydown.enter.prevent="sendQuestion" />
            <div class="question-toolbar">
              <div class="deep-think-toggle" :class="{ on: deepThink }" @click="deepThink = !deepThink">
                <el-icon><MagicStick /></el-icon><span>深度思考</span><span v-if="deepThink" class="think-dot"></span>
              </div>
              <div v-if="isLoading" class="stop-btn" @click="stopStream"><el-icon><VideoPause /></el-icon></div>
              <div v-else class="send-btn" :class="{ disabled: !question.trim() }" @click="sendQuestion"><el-icon><Promotion /></el-icon></div>
            </div>
          </div>
          <div v-if="deepThink" class="deep-think-tip"><el-icon><Opportunity /></el-icon><span>深度思考模式已开启</span></div>
          <div class="input-hint"><kbd>Enter</kbd><span>发送</span><span class="dot">·</span><kbd>Shift + Enter</kbd><span>换行</span></div>
        </div>
      </div>
    </el-main>
  </el-container>
</template>
 
<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import {
  ChatDotRound, Plus, Setting, HomeFilled,
  MagicStick, Promotion, Notebook, CircleCheck, Opportunity, TopRight, VideoPause
} from '@element-plus/icons-vue'
 
const question = ref('')
const deepThink = ref(false)
const isLoading = ref(false)
const messages = ref([])
const messageListRef = ref(null)
 
// ========== 会话管理 ==========
const API_BASE = 'http://localhost:8000/v1/chat'
const WS_URL = 'ws://localhost:8000/v1/chat/ws'
const currentSessionId = ref(null)   // 当前会话 ID
const sessions = ref([])             // 左侧历史会话列表
 
let ws = null
let currentAssistantMsg = null
 
// ---- WebSocket ----
 
const connectWs = () => {
  if (ws && ws.readyState === WebSocket.OPEN) return
  ws = new WebSocket(WS_URL)
 
  ws.onmessage = (event) => {
    try {
      const json = JSON.parse(event.data)
 
      if (json.event === 'chunk') {
        if (!currentAssistantMsg) return
        currentAssistantMsg.content += json.data
        scrollToBottom()
 
      } else if (json.event === 'done') {
        isLoading.value = false
        currentAssistantMsg = null
        refreshSessions()
 
      } else if (json.event === 'stopped') {
        isLoading.value = false
        currentAssistantMsg = null
 
      } else if (json.event === 'error') {
        console.error('WS error:', json.data)
        isLoading.value = false
        currentAssistantMsg = null
 
      } else if (json.event === 'session_created') {
        // 后端自动创建了新会话
        currentSessionId.value = json.data.session_id
        refreshSessions()
 
      } else if (json.event === 'history') {
        // 后端推送了历史消息
        const historyMsgs = json.data.map(m => ({
          id: m.id,
          role: m.role,
          content: m.content
        }))
        messages.value = historyMsgs
      }
    } catch (e) {}
  }
 
  ws.onclose = () => { isLoading.value = false; currentAssistantMsg = null }
  ws.onerror = () => { isLoading.value = false; currentAssistantMsg = null }
}
 
const disconnectWs = () => { if (ws) { ws.close(); ws = null } }
onMounted(() => { connectWs(); refreshSessions() })
onUnmounted(() => disconnectWs())
 
// ---- REST: 会话列表 ----
 
const refreshSessions = async () => {
  try {
    const res = await fetch(`${API_BASE}/sessions`)
    const data = await res.json()
    sessions.value = data.sessions || []
  } catch (e) {
    console.error('获取会话列表失败:', e)
  }
}
 
// ---- 切换会话 ----
 
const switchSession = (sessionId) => {
  if (sessionId === currentSessionId.value) return
  currentSessionId.value = sessionId
  messages.value = []
  currentAssistantMsg = null
  isLoading.value = false
  question.value = ''
  // 通知后端加载历史
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'chat', session_id: sessionId }))
  }
}
 
// ---- 新建对话 ----
 
const startNewChat = () => {
  if (isLoading.value) stopStream()
  question.value = ''
  messages.value = []
  isLoading.value = false
  currentAssistantMsg = null
  currentSessionId.value = null
  // 重连保证干净
  disconnectWs()
  connectWs()
}
 
// ---- 发送消息 ----
 
const sendWsChat = (payload) => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connectWs()
    ws.onopen = () => ws.send(JSON.stringify(payload))
    return
  }
  ws.send(JSON.stringify(payload))
}
 
const stopStream = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop' }))
  }
  isLoading.value = false
  currentAssistantMsg = null
}
 
const sendQuestion = async () => {
  const msg = question.value.trim()
  if (!msg || isLoading.value) return
 
  messages.value.push({ id: Date.now(), role: 'user', content: msg })
  question.value = ''
  scrollToBottom()
 
  const assistantMsg = reactive({ id: Date.now() + 1, role: 'assistant', content: '' })
  messages.value.push(assistantMsg)
  currentAssistantMsg = assistantMsg
 
  isLoading.value = true
  const modelType = deepThink.value ? 'qwen_api' : 'ollama'
 
  sendWsChat({
    type: 'chat',
    message: msg,
    session_id: currentSessionId.value,
    model_type: modelType
  })
}
 
// ---- 工具函数 ----
 
const hasMessages = computed(() => messages.value.length > 0)
const inputPlaceholder = computed(() => deepThink.value ? '输入需要深度分析的问题...' : '询问助手是做什么的、是谁、能做什么等')
 
const starterCards = [
  { icon: Notebook, iconBg: '#eef2ff', iconColor: '#6366f1', title: '实时数据', subtitle: '销售汇总数据统计', hintLabel: '推荐问法：销售数据统计...', hint: '销售数据统计，如：销售总额、销售趋势' },
  { icon: CircleCheck, iconBg: '#e8f6ef', iconColor: '#22a06b', title: '业务系统', subtitle: '数据安全', hintLabel: '推荐问法：数据权限、访问控制...', hint: '数据权限、访问控制、安全策略' },
  { icon: Opportunity, iconBg: '#fef6e7', iconColor: '#e0a020', title: '系统交互', subtitle: '关于助手', hintLabel: '推荐问法：询问助手是做什么的...', hint: '询问助手是做什么的、是谁、能做什么等' }
]
 
const fillInput = (text) => { question.value = text }
 
const scrollToBottom = () => {
  nextTick(() => {
    const el = messageListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
</script>
 
<style scoped>
* { box-sizing: border-box; }
.app-container { height: 100vh; background: radial-gradient(circle at 30% 20%, #eef2fb 0%, #f4f6fb 45%, #eef1f7 100%); }
 
.sidebar { background: #ffffff; border-right: 1px solid #ececf0; display: flex; flex-direction: column; padding: 22px 16px 16px 16px; }
.logo-area { display: flex; align-items: center; gap: 10px; padding: 0 4px 20px 4px; }
.logo-icon { width: 34px; height: 34px; border-radius: 9px; background: linear-gradient(135deg, #4f7fff, #6a5cf5); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 17px; flex-shrink: 0; }
.logo-text { display: flex; flex-direction: column; line-height: 1.3; }
.logo-title { font-size: 15px; font-weight: 700; color: #1d2129; }
.logo-sub { font-size: 11px; color: #9aa3b2; }
 
.quick-start-card { background: linear-gradient(135deg, #fdf7ec 0%, #fbf1e4 100%); border-radius: 14px; padding: 14px 14px 12px 14px; margin-bottom: 10px; }
.quick-start-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.quick-start-label { font-size: 12px; font-weight: 600; color: #8a8375; }
.quick-start-badge { font-size: 11px; color: #4f7fff; background: #eaf0ff; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.new-chat-row { display: flex; align-items: center; gap: 10px; background: #ffffff; border-radius: 10px; padding: 8px 10px; cursor: pointer; transition: box-shadow 0.2s; }
.new-chat-row:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.new-chat-icon { width: 30px; height: 30px; border-radius: 50%; background: #4f7fff; color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.new-chat-text { display: flex; flex-direction: column; line-height: 1.3; }
.new-chat-title { font-size: 13.5px; font-weight: 600; color: #1d2129; }
.new-chat-sub { font-size: 11px; color: #9aa3b2; }
 
.history-section { flex: 1; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #d5dae2 transparent; }
.history-section::-webkit-scrollbar { width: 5px; }
.history-section::-webkit-scrollbar-track { background: transparent; }
.history-section::-webkit-scrollbar-thumb { background: #e0e3e9; border-radius: 3px; }
.history-label { font-size: 12px; color: #b0b8c4; padding: 4px 6px 8px 6px; }
.history-list { list-style: none; margin: 0; padding: 0; }
.history-item { font-size: 13.5px; color: #4e5969; padding: 9px 8px; border-radius: 8px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: background 0.15s; }
.history-item:hover { background: #f5f6f9; }
.history-item.active { background: #eef2ff; color: #4f7fff; font-weight: 500; }
.history-item-empty { font-size: 12.5px; color: #b0b8c4; padding: 9px 8px; }
 
.user-info { display: flex; align-items: center; gap: 10px; padding: 14px 6px 0 6px; border-top: 1px solid #f0f2f5; font-size: 14px; color: #303133; margin-top: 10px; }
.user-name { flex: 1; }
 
.main-content { display: flex; flex-direction: column; padding: 0 40px 30px 40px; overflow: hidden; }
.top-bar { display: flex; align-items: center; padding: 22px 0 10px 0; flex-shrink: 0; }
.top-bar-new-chat { font-size: 14px; color: #1d2129; font-weight: 500; cursor: pointer; }
.top-bar-new-chat:hover { color: #4f7fff; }
 
.hero-wrap { width: 100%; max-width: 820px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; padding-top: 60px; overflow-y: auto; }
.hero-badge { display: flex; align-items: center; gap: 6px; background: #ffffff; border: 1px solid #eef0f4; color: #606773; font-size: 12.5px; padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 26px; }
.hero-badge .el-icon { color: #4f7fff; }
.hero-title { font-size: 46px; font-weight: 700; color: #1d2129; text-align: center; margin: 0 0 16px 0; line-height: 1.3; }
.hero-highlight { color: #4f7fff; }
.hero-sub { font-size: 16px; color: #6b7280; text-align: center; margin: 0 0 36px 0; }
 
.question-card { width: 100%; background: #ffffff; border: 1px solid #dbe4fb; border-radius: 18px; padding: 18px 20px 12px 20px; box-shadow: 0 8px 30px rgba(79,127,255,0.08); }
.question-input :deep(.el-textarea__inner) { border: none; padding: 0; font-size: 15.5px; box-shadow: none; resize: none; color: #1d2129; }
.question-input :deep(.el-textarea__inner:focus) { box-shadow: none; }
.question-toolbar { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.deep-think-toggle { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #606773; background: #f5f6f9; border-radius: 16px; padding: 6px 14px; cursor: pointer; transition: all 0.2s; }
.deep-think-toggle.on { background: #eaf0ff; color: #4f7fff; }
.think-dot { width: 6px; height: 6px; border-radius: 50%; background: #4f7fff; }
.send-btn { width: 34px; height: 34px; border-radius: 50%; background: #4f7fff; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.2s; }
.send-btn:hover { background: #3f6bee; }
.send-btn.disabled { background: #cdd6f2; cursor: not-allowed; }
.stop-btn { width: 34px; height: 34px; border-radius: 50%; background: #f56c6c; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.2s; }
.stop-btn:hover { background: #e04848; }
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
 
/* ===== 对话视图 ===== */
.chat-wrap { flex: 1; display: flex; flex-direction: column; width: 100%; max-width: 900px; margin: 0 auto; min-height: 0; }
.message-list { flex: 1; overflow-y: auto; padding: 10px 4px 20px 4px; display: flex; flex-direction: column; gap: 18px; scrollbar-width: thin; scrollbar-color: #d5dae2 transparent; }
.message-list::-webkit-scrollbar { width: 6px; }
.message-list::-webkit-scrollbar-track { background: transparent; }
.message-list::-webkit-scrollbar-thumb { background: #d5dae2; border-radius: 3px; }
.chat-input-bar { flex-shrink: 0; padding-top: 8px; padding-bottom: 4px; background: linear-gradient(to top, #f2f4fa 60%, rgba(242,244,250,0)); }
 
.user-bubble-row { display: flex; justify-content: flex-end; }
.user-bubble { max-width: 70%; background: #d8e6ff; color: black; font-size: 14.5px; line-height: 1.6; padding: 10px 16px; border-radius: 16px 16px 4px 16px; white-space: pre-wrap; word-break: break-word; }
.assistant-row { display: flex; justify-content: flex-start; }
.assistant-text { max-width: 80%; font-size: 14.5px; line-height: 1.7; color: #1d2129; white-space: pre-wrap; word-break: break-word; }
.assistant-thinking { display: flex; align-items: center; gap: 5px; padding: 4px 0; }
.think-jump { width: 6px; height: 6px; border-radius: 50%; background: #c2c8d1; animation: think-jump-anim 1.1s infinite ease-in-out; }
.think-jump:nth-child(2) { animation-delay: 0.15s; }
.think-jump:nth-child(3) { animation-delay: 0.3s; }
@keyframes think-jump-anim { 0%,60%,100% { transform: translateY(0); opacity: 0.5; } 30% { transform: translateY(-4px); opacity: 1; } }
</style>