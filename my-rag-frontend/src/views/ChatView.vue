<template>
  <el-container class="app-container">
    <!-- 左侧边栏 -->
    <el-aside width="270px" class="sidebar">
      <!-- Logo -->
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon><ChatDotRound /></el-icon>
        </div>
        <div class="logo-text">
          <span class="logo-title">RAG 智能问答</span>
          <span class="logo-sub">Powered by AI</span>
        </div>
      </div>
 
      <!-- 快速开始卡片 -->
      <div class="quick-start-card">
        <div class="quick-start-top">
          <span class="quick-start-label">快速开始</span>
          <span class="quick-start-badge">新内容</span>
        </div>
        <div class="new-chat-row" @click="startNewChat">
          <div class="new-chat-icon">
            <el-icon><Plus /></el-icon>
          </div>
          <div class="new-chat-text">
            <span class="new-chat-title">新建对话</span>
            <span class="new-chat-sub">从空白开始</span>
          </div>
        </div>
      </div>
 
      <div class="admin-row">
        <el-icon><Setting /></el-icon>
        <span>管理后台</span>
      </div>
 
      <!-- 搜索对话 -->
      <div class="search-wrap">
        <el-input
          v-model="searchQuery"
          placeholder="搜索对话"
          :prefix-icon="Search"
          clearable
          class="search-input"
        >
          <template #suffix>
            <span class="search-kbd">Ctrl / Cmd + K</span>
          </template>
        </el-input>
      </div>
 
      <!-- 历史对话列表 -->
      <div class="history-section">
        <div class="history-label">更早</div>
        <ul class="history-list">
          <li
            v-for="item in historyList"
            :key="item"
            class="history-item"
            :class="{ active: item === activeHistory }"
            @click="activeHistory = item"
          >
            {{ item }}
          </li>
        </ul>
      </div>
 
      <!-- 用户信息 -->
      <div class="user-info">
        <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a53f6f0f6dpng.png" />
        <span class="user-name">admin</span>
        <el-icon class="user-more"><MoreFilled /></el-icon>
      </div>
    </el-aside>
 
    <!-- 主内容区 -->
    <el-main class="main-content">
      <!-- 顶部栏：进入对话后出现 -->
      <div v-if="hasMessages" class="top-bar">
        <div class="top-bar-new-chat" @click="startNewChat">新对话</div>
      </div>
 
      <!-- ========== 首页 Hero（未发送任何消息时） ========== -->
      <div v-if="!hasMessages" class="hero-wrap">
        <div class="hero-badge">
          <el-icon><HomeFilled /></el-icon>
          <span>RAG 智能问答</span>
        </div>
 
        <h1 class="hero-title">
          把问题变成<span class="hero-highlight">清晰答案</span>
        </h1>
        <p class="hero-sub">结构化提问、知识检索与深度思考，一次对话给出可执行方案</p>
 
        <!-- 输入卡片 -->
        <div class="question-card">
          <el-input
            v-model="question"
            type="textarea"
            :rows="2"
            :placeholder="inputPlaceholder"
            class="question-input"
            resize="none"
            @keydown.enter.prevent="sendQuestion"
          />
          <div class="question-toolbar">
            <div class="deep-think-toggle" :class="{ on: deepThink }" @click="deepThink = !deepThink">
              <el-icon><MagicStick /></el-icon>
              <span>深度思考</span>
              <span v-if="deepThink" class="think-dot"></span>
            </div>
            <div class="send-btn" :class="{ disabled: !question.trim() || isLoading }" @click="sendQuestion">
              <el-icon><Promotion /></el-icon>
            </div>
          </div>
        </div>
 
        <div v-if="deepThink" class="deep-think-tip">
          <el-icon><Opportunity /></el-icon>
          <span>深度思考模式已开启，AI将进行更深入的分析推理</span>
        </div>
 
        <div class="input-hint">
          <kbd>Enter</kbd><span>发送</span>
          <span class="dot">·</span>
          <kbd>Shift + Enter</kbd><span>换行</span>
        </div>
 
        <!-- 分割线 -->
        <div class="divider-row">
          <span class="divider-line"></span>
          <span class="divider-text">试试这些开场</span>
          <span class="divider-line"></span>
        </div>
 
        <!-- 开场卡片 -->
        <div class="starter-cards">
          <div
            v-for="card in starterCards"
            :key="card.title"
            class="starter-card"
            @click="fillInput(card.hint)"
          >
            <div class="starter-card-top">
              <div class="starter-icon" :style="{ background: card.iconBg, color: card.iconColor }">
                <el-icon><component :is="card.icon" /></el-icon>
              </div>
              <el-icon class="starter-arrow"><TopRight /></el-icon>
            </div>
            <div class="starter-title">{{ card.title }}</div>
            <div class="starter-sub">{{ card.subtitle }}</div>
            <div class="starter-hint">{{ card.hintLabel }}</div>
          </div>
        </div>
      </div>
 
      <!-- ========== 对话视图（发送消息后） ========== -->
      <div v-else class="chat-wrap">
        <div class="message-list" ref="messageListRef">
          <template v-for="msg in messages" :key="msg.id">
            <div v-if="msg.role === 'user'" class="user-bubble-row">
              <div class="user-bubble">{{ msg.content }}</div>
            </div>
            <div v-else class="assistant-row">
              <div v-if="!msg.content && isLoading" class="assistant-thinking">
                <span class="think-jump"></span>
                <span class="think-jump"></span>
                <span class="think-jump"></span>
              </div>
              <div v-else class="assistant-text">{{ msg.content }}</div>
            </div>
          </template>
        </div>
 
        <!-- 底部固定输入区 -->
        <div class="chat-input-bar">
          <div class="question-card">
            <el-input
              v-model="question"
              type="textarea"
              :rows="2"
              :placeholder="inputPlaceholder"
              class="question-input"
              resize="none"
              @keydown.enter.prevent="sendQuestion"
            />
            <div class="question-toolbar">
              <div class="deep-think-toggle" :class="{ on: deepThink }" @click="deepThink = !deepThink">
                <el-icon><MagicStick /></el-icon>
                <span>深度思考</span>
                <span v-if="deepThink" class="think-dot"></span>
              </div>
              <!-- 生成中 → 显示暂停按钮；未生成 → 显示发送按钮 -->
              <div v-if="isLoading" class="stop-btn" @click="stopStream">
                <el-icon><VideoPause /></el-icon>
              </div>
              <div v-else class="send-btn" :class="{ disabled: !question.trim() }" @click="sendQuestion">
                <el-icon><Promotion /></el-icon>
              </div>
            </div>
          </div>
 
          <div v-if="deepThink" class="deep-think-tip">
            <el-icon><Opportunity /></el-icon>
            <span>深度思考模式已开启，AI将进行更深入的分析推理</span>
          </div>
 
          <div class="input-hint">
            <kbd>Enter</kbd><span>发送</span>
            <span class="dot">·</span>
            <kbd>Shift + Enter</kbd><span>换行</span>
          </div>
        </div>
      </div>
    </el-main>
  </el-container>
</template>
 
<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import {
  ChatDotRound,
  Plus,
  Setting,
  Search,
  MoreFilled,
  HomeFilled,
  MagicStick,
  Promotion,
  Notebook,
  CircleCheck,
  Opportunity,
  TopRight,
  Star,
  VideoPause
} from '@element-plus/icons-vue'
 
// 搜索关键词
const searchQuery = ref('')
 
// 输入框内容
const question = ref('')
 
// 深度思考开关
const deepThink = ref(false)
 
// 当前选中的历史对话
const activeHistory = ref('')
 
// 请求加载状态
const isLoading = ref(false)
 
// 对话消息列表：{ id, role: 'user' | 'assistant', content }
const messages = ref([])
const messageListRef = ref(null)
 
// ========== WebSocket ==========
const WS_URL = 'ws://localhost:8000/v1/chat/ws'
let ws = null
// 当前助手消息引用——流式推送时直接往它身上追加内容
let currentAssistantMsg = null
 
/** 建立 WebSocket 连接（页面挂载时调用一次） */
const connectWs = () => {
  if (ws && ws.readyState === WebSocket.OPEN) return
 
  ws = new WebSocket(WS_URL)
 
  ws.onmessage = (event) => {
    try {
      const json = JSON.parse(event.data)
      if (json.event === 'chunk') {
        if (!currentAssistantMsg) return
        currentAssistantMsg.content += json.data
        // 去掉开头的回显（部分后端会把用户原话带回来）
        const userMsg = messages.value.find(m => m.id === currentAssistantMsg.id - 1)
        if (userMsg && currentAssistantMsg.content.startsWith(userMsg.content)) {
          currentAssistantMsg.content = currentAssistantMsg.content
            .slice(userMsg.content.length)
            .replace(/^[\s:：\n]+/, '')
        }
        scrollToBottom()
      } else if (json.event === 'done') {
        isLoading.value = false
        currentAssistantMsg = null
      } else if (json.event === 'stopped') {
        isLoading.value = false
        currentAssistantMsg = null
      } else if (json.event === 'error') {
        console.error('WS error:', json.data)
        isLoading.value = false
        currentAssistantMsg = null
      }
    } catch (e) {
      // ignore
    }
  }
 
  ws.onclose = () => {
    isLoading.value = false
    currentAssistantMsg = null
  }
 
  ws.onerror = () => {
    isLoading.value = false
    currentAssistantMsg = null
  }
}
 
/** 断开 WebSocket */
const disconnectWs = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}
 
onMounted(() => {
  connectWs()
})
 
onUnmounted(() => {
  disconnectWs()
})
 
// 是否已进入对话视图
const hasMessages = computed(() => messages.value.length > 0)
 
// 输入框占位文案：开启深度思考后文案更聚焦分析类问题
const inputPlaceholder = computed(() =>
  deepThink.value ? '输入需要深度分析的问题...' : '询问助手是做什么的、是谁、能做什么等'
)
 
// 左侧历史对话列表
const historyList = [
  'Ragent AI相比普通RAG的优势',
  '销售数据统计指标',
  '杭州未来几天天气',
  '公司福利有哪些',
  '新员工培训流程',
  '阿里巴巴发票抬头',
  '打印机使用方法',
  'VPN使用方法',
  '助手的功能与身份介绍',
  '校招流程',
  'OA系统数据安全措施'
]
 
// 底部三个开场引导卡片
const starterCards = [
  {
    icon: Notebook,
    iconBg: '#eef2ff',
    iconColor: '#6366f1',
    title: '实时数据',
    subtitle: '销售汇总数据统计',
    hintLabel: '推荐问法：销售数据统计，如：销售总...',
    hint: '销售数据统计，如：销售总额、销售趋势'
  },
  {
    icon: CircleCheck,
    iconBg: '#e8f6ef',
    iconColor: '#22a06b',
    title: '业务系统',
    subtitle: '数据安全',
    hintLabel: '推荐问法：数据权限、访问控制、安全...',
    hint: '数据权限、访问控制、安全策略'
  },
  {
    icon: Opportunity,
    iconBg: '#fef6e7',
    iconColor: '#e0a020',
    title: '系统交互',
    subtitle: '关于助手',
    hintLabel: '推荐问法：询问助手是做什么的、是谁...',
    hint: '询问助手是做什么的、是谁、能做什么等'
  }
]
 
// 点击卡片/标签填充输入框
const fillInput = (text) => {
  question.value = text
}
 
// 新建对话：清空消息、回到首页
const startNewChat = () => {
  // 先停掉正在生成的流
  if (isLoading.value) {
    stopStream()
  }
  question.value = ''
  activeHistory.value = ''
  messages.value = []
  isLoading.value = false
  currentAssistantMsg = null
  // 重连（保证连接干净）
  disconnectWs()
  connectWs()
}
 
// 滚动消息列表到底部
const scrollToBottom = () => {
  nextTick(() => {
    const el = messageListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
 
/** 发送 WebSocket chat 消息 */
const sendWsChat = (msg, modelType) => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    // 尝试重连
    connectWs()
    // 如果连接还没建好，延迟再发
    const trySend = () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'chat', message: msg, model_type: modelType }))
      } else {
        setTimeout(trySend, 200)
      }
    }
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'chat', message: msg, model_type: modelType }))
    }
    // 如果已经 OPEN 了但 onopen 不会再触发，直接发
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'chat', message: msg, model_type: modelType }))
    }
    return
  }
  ws.send(JSON.stringify({ type: 'chat', message: msg, model_type: modelType }))
}
 
/** 发送 stop 消息暂停生成 */
const stopStream = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop' }))
  }
  isLoading.value = false
  currentAssistantMsg = null
}
 
// 发送问题并对接后端 WebSocket
const sendQuestion = async () => {
  const msg = question.value.trim()
  if (!msg || isLoading.value) return
 
  // 1. 先把用户消息放进对话列表，输入框清空，视图自动切换到对话态
  messages.value.push({ id: Date.now(), role: 'user', content: msg })
  question.value = ''
  scrollToBottom()
 
  // 2. 占位的助手消息，用于流式追加内容
  const assistantMsg = reactive({ id: Date.now() + 1, role: 'assistant', content: '' })
  messages.value.push(assistantMsg)
  currentAssistantMsg = assistantMsg
 
  isLoading.value = true
  const modelType = deepThink.value ? 'qwen_api' : 'ollama'
 
  sendWsChat(msg, modelType)
}
</script>
 
<style scoped>
* {
  box-sizing: border-box;
}
 
.app-container {
  height: 100vh;
  background: radial-gradient(circle at 30% 20%, #eef2fb 0%, #f4f6fb 45%, #eef1f7 100%);
}
 
/* ===== 左侧边栏 ===== */
.sidebar {
  background: #ffffff;
  border-right: 1px solid #ececf0;
  display: flex;
  flex-direction: column;
  padding: 22px 16px 16px 16px;
}
 
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px 20px 4px;
}
 
.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, #4f7fff, #6a5cf5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 17px;
  flex-shrink: 0;
}
 
.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
 
.logo-title {
  font-size: 15px;
  font-weight: 700;
  color: #1d2129;
}
 
.logo-sub {
  font-size: 11px;
  color: #9aa3b2;
}
 
/* 快速开始卡片 */
.quick-start-card {
  background: linear-gradient(135deg, #fdf7ec 0%, #fbf1e4 100%);
  border-radius: 14px;
  padding: 14px 14px 12px 14px;
  margin-bottom: 10px;
}
 
.quick-start-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
 
.quick-start-label {
  font-size: 12px;
  font-weight: 600;
  color: #8a8375;
}
 
.quick-start-badge {
  font-size: 11px;
  color: #4f7fff;
  background: #eaf0ff;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
 
.new-chat-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #ffffff;
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.new-chat-row:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
 
.new-chat-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #4f7fff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
 
.new-chat-text {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
 
.new-chat-title {
  font-size: 13.5px;
  font-weight: 600;
  color: #1d2129;
}
 
.new-chat-sub {
  font-size: 11px;
  color: #9aa3b2;
}
 
.admin-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606773;
  padding: 8px 6px 16px 6px;
  cursor: pointer;
}
.admin-row:hover {
  color: #4f7fff;
}
 
.search-wrap {
  margin-bottom: 14px;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: #f5f6f9;
  box-shadow: none;
  padding: 4px 10px;
}
.search-kbd {
  font-size: 10.5px;
  color: #b0b8c4;
  white-space: nowrap;
}
 
.history-section {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #d5dae2 transparent;
}
.history-section::-webkit-scrollbar {
  width: 5px;
}
.history-section::-webkit-scrollbar-track {
  background: transparent;
}
.history-section::-webkit-scrollbar-thumb {
  background: #e0e3e9;
  border-radius: 3px;
}
 
.history-label {
  font-size: 12px;
  color: #b0b8c4;
  padding: 4px 6px 8px 6px;
}
 
.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
 
.history-item {
  font-size: 13.5px;
  color: #4e5969;
  padding: 9px 8px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s;
}
.history-item:hover {
  background: #f5f6f9;
}
.history-item.active {
  background: #eef2ff;
  color: #4f7fff;
  font-weight: 500;
}
 
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 6px 0 6px;
  border-top: 1px solid #f0f2f5;
  font-size: 14px;
  color: #303133;
  margin-top: 10px;
}
.user-name {
  flex: 1;
}
.user-more {
  color: #b0b8c4;
  cursor: pointer;
}
 
/* ===== 主内容区 ===== */
.main-content {
  display: flex;
  flex-direction: column;
  padding: 0 40px 30px 40px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #d5dae2 transparent;
}
.main-content::-webkit-scrollbar {
  width: 6px;
}
.main-content::-webkit-scrollbar-track {
  background: transparent;
}
.main-content::-webkit-scrollbar-thumb {
  background: #d5dae2;
  border-radius: 3px;
}
.main-content::-webkit-scrollbar-thumb:hover {
  background: #b9c0cc;
}
 
/* 顶部栏（对话态） */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 0 10px 0;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 5;
  background: #f2f4fa;
}
.top-bar-new-chat {
  font-size: 14px;
  color: #1d2129;
  font-weight: 500;
  cursor: pointer;
}
.top-bar-new-chat:hover {
  color: #4f7fff;
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.star-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid #eef0f4;
  border-radius: 16px;
  padding: 5px 12px;
  font-size: 12.5px;
  color: #606773;
}
.star-badge .el-icon {
  color: #f2b93d;
}
.top-more {
  color: #b0b8c4;
  cursor: pointer;
  font-size: 16px;
}
 
.hero-wrap {
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60px;
  flex-shrink: 0;
}
 
.hero-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid #eef0f4;
  color: #606773;
  font-size: 12.5px;
  padding: 6px 14px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 26px;
}
.hero-badge .el-icon {
  color: #4f7fff;
}
 
.hero-title {
  font-size: 46px;
  font-weight: 700;
  color: #1d2129;
  text-align: center;
  margin: 0 0 16px 0;
  line-height: 1.3;
}
.hero-highlight {
  color: #4f7fff;
}
 
.hero-sub {
  font-size: 16px;
  color: #6b7280;
  text-align: center;
  margin: 0 0 36px 0;
}
 
/* 输入卡片（首页与对话底部共用样式） */
.question-card {
  width: 100%;
  background: #ffffff;
  border: 1px solid #dbe4fb;
  border-radius: 18px;
  padding: 18px 20px 12px 20px;
  box-shadow: 0 8px 30px rgba(79, 127, 255, 0.08);
}
 
.question-input :deep(.el-textarea__inner) {
  border: none;
  padding: 0;
  font-size: 15.5px;
  box-shadow: none;
  resize: none;
  color: #1d2129;
}
.question-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}
 
.question-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
 
.deep-think-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: #606773;
  background: #f5f6f9;
  border-radius: 16px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.deep-think-toggle.on {
  background: #eaf0ff;
  color: #4f7fff;
}
.think-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4f7fff;
}
 
.send-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #4f7fff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}
.send-btn:hover {
  background: #3f6bee;
}
.send-btn.disabled {
  background: #cdd6f2;
  cursor: not-allowed;
}
 
/* 暂停按钮样式：红色圆形，与发送按钮对称 */
.stop-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #f56c6c;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}
.stop-btn:hover {
  background: #e04848;
}
 
.deep-think-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: #4f7fff;
  margin-top: 12px;
  width: 100%;
}
 
.input-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: #b0b8c4;
  margin: 12px 0 34px 0;
}
.input-hint .dot {
  color: #d5dae2;
}
.input-hint kbd {
  background: #f0f1f5;
  border-radius: 4px;
  padding: 2px 7px;
  font-family: inherit;
  font-size: 11px;
  color: #606773;
}
 
/* 分割线 */
.divider-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  max-width: 340px;
  margin-bottom: 26px;
}
.divider-line {
  flex: 1;
  height: 1px;
  background: #e5e8ef;
}
.divider-text {
  font-size: 12.5px;
  color: #9aa3b2;
  white-space: nowrap;
}
 
/* 开场卡片 */
.starter-cards {
  display: flex;
  gap: 20px;
  width: 100%;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
 
.starter-card {
  flex: 1;
  min-width: 220px;
  background: #ffffff;
  border-radius: 14px;
  padding: 18px 18px 16px 18px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.starter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}
 
.starter-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
 
.starter-icon {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
 
.starter-arrow {
  color: #c2c8d1;
  font-size: 14px;
}
 
.starter-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}
 
.starter-sub {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 10px;
}
 
.starter-hint {
  font-size: 12px;
  color: #b0b8c4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
 
/* ========== 对话视图 ========== */
.chat-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}
 
.message-list {
  flex: 1;
  padding: 10px 4px 20px 4px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
 
.user-bubble-row {
  display: flex;
  justify-content: flex-end;
}
.user-bubble {
  max-width: 70%;
  background: #d8e6ff;
  color: black;
  font-size: 14.5px;
  line-height: 1.6;
  padding: 10px 16px;
  border-radius: 16px 16px 4px 16px;
  white-space: pre-wrap;
  word-break: break-word;
}
 
.assistant-row {
  display: flex;
  justify-content: flex-start;
}
.assistant-text {
  max-width: 80%;
  font-size: 14.5px;
  line-height: 1.7;
  color: #1d2129;
  white-space: pre-wrap;
  word-break: break-word;
}
 
.assistant-thinking {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 0;
}
.think-jump {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c2c8d1;
  animation: think-jump-anim 1.1s infinite ease-in-out;
}
.think-jump:nth-child(2) {
  animation-delay: 0.15s;
}
.think-jump:nth-child(3) {
  animation-delay: 0.3s;
}
@keyframes think-jump-anim {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
 
/* 对话态底部固定输入区：吸附在可视区域底部 */
.chat-input-bar {
  flex-shrink: 0;
  position: sticky;
  bottom: 0;
  padding-top: 8px;
  padding-bottom: 4px;
  background: linear-gradient(to top, #f2f4fa 60%, rgba(242, 244, 250, 0));
}
</style>