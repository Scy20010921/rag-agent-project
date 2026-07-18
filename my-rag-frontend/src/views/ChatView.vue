<template>
  <el-container class="app-container">
    <Sidebar
      :hasMessages="hasMessages"
      :sessions="sessions"
      :currentSessionId="currentSessionId"
      :documents="docs"
      @newChat="handleNewChat"
      @switchSession="handleSwitchSession"
      @uploadDone="refreshDocs"
      @deleteDoc="handleDeleteDoc"
    />

    <el-main class="main-content">
      <div v-if="hasMessages" class="top-bar">
        <div class="top-bar-new-chat" @click="handleNewChat">新对话</div>
        <div class="top-bar-right">
          <div class="prompt-btn" @click="showPromptDialog = true">
            <el-icon><EditPen /></el-icon>
            <span>系统提示词</span>
          </div>
        </div>
      </div>

      <HeroView
        v-if="!hasMessages"
        :question="question"
        :deepThink="deepThink"
        :isLoading="isLoading"
        :inputPlaceholder="inputPlaceholder"
        @send="sendQuestion"
        @fillInput="question = $event"
        @update:question="question = $event"
        @update:deepThink="deepThink = $event"
      />

      <div v-if="!hasMessages" class="prompt-hint-row">
        <div class="prompt-hint" @click="showPromptDialog = true">
          <el-icon><Setting /></el-icon>
          <span>{{ systemPrompt ? '已设置系统提示词' : '点击设置系统提示词（定义AI角色）' }}</span>
        </div>
      </div>

      <ChatView_
        v-else
        ref="chatViewRef"
        :question="question"
        :deepThink="deepThink"
        :isLoading="isLoading"
        :inputPlaceholder="inputPlaceholder"
        :messages="messages"
        :currentAssistantMsg="chat.currentAssistantMsg"
        @send="sendQuestion"
        @stop="stopStream"
        @update:question="question = $event"
        @update:deepThink="deepThink = $event"
      />

      <SystemPromptDialog
        v-model="showPromptDialog"
        :systemPrompt="systemPrompt"
        @save="systemPrompt = $event"
      />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { EditPen, Setting } from '@element-plus/icons-vue'
import Sidebar from '../components/Sidebar.vue'
import HeroView from '../components/HeroView.vue'
import ChatView_ from '../components/ChatView_.vue'
import SystemPromptDialog from '../components/SystemPromptDialog.vue'
import { useSessions } from '../composables/useSessions'
import { useChat } from '../composables/useChat'

const API_BASE = 'http://localhost:8000/v1'
const question = ref('')
const deepThink = ref(false)
const systemPrompt = ref('')
const showPromptDialog = ref(false)
const chatViewRef = ref(null)
const docs = ref([])

const getScrollEl = () => chatViewRef.value?.messageListRef || null
const { sessions, currentSessionId, refreshSessions, switchSession, startNewChat } = useSessions()
const chat = useChat(question, deepThink, { currentSessionId, refreshSessions }, systemPrompt, getScrollEl)

const {
  isLoading, messages, hasMessages, inputPlaceholder,
  connectWs, disconnectWs, stopStream, sendQuestion, resetMessages,
} = chat

onMounted(() => {
  connectWs()
  refreshSessions()
  refreshDocs()
})
onUnmounted(() => disconnectWs())

// ---- 文档管理 ----

const refreshDocs = async () => {
  try {
    const res = await fetch(`${API_BASE}/documents`)
    const data = await res.json()
    docs.value = data.documents || []
  } catch (e) {
    console.error('获取文档列表失败:', e)
  }
}

const handleDeleteDoc = async (docId) => {
  try {
    await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' })
    refreshDocs()
  } catch (e) {
    console.error('删除文档失败:', e)
  }
}

// ---- 会话 ----

const handleNewChat = () => {
  if (isLoading.value) stopStream()
  question.value = ''
  resetMessages()
  startNewChat(() => { disconnectWs(); connectWs() })
}

const handleSwitchSession = (sid) => {
  switchSession(sid, () => {
    resetMessages()
    question.value = ''
    chat.ws_send({ type: 'chat', session_id: sid })
  })
}
</script>

<style scoped>
.app-container { height: 100vh; background: radial-gradient(circle at 30% 20%, #eef2fb 0%, #f4f6fb 45%, #eef1f7 100%); }
.main-content { display: flex; flex-direction: column; padding: 0 40px 30px 40px; overflow: hidden; }
.top-bar { display: flex; align-items: center; justify-content: space-between; padding: 22px 0 10px 0; flex-shrink: 0; }
.top-bar-new-chat { font-size: 14px; color: #1d2129; font-weight: 500; cursor: pointer; }
.top-bar-new-chat:hover { color: #4f7fff; }
.top-bar-right { display: flex; align-items: center; gap: 14px; }
.prompt-btn { display: flex; align-items: center; gap: 5px; font-size: 13px; color: #606773; background: #ffffff; border: 1px solid #eef0f4; border-radius: 16px; padding: 5px 14px; cursor: pointer; transition: all 0.2s; }
.prompt-btn:hover { color: #4f7fff; border-color: #c7d2fe; }
.prompt-hint-row { width: 100%; max-width: 820px; margin: 0 auto; display: flex; justify-content: center; padding-top: 18px; }
.prompt-hint { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #9aa3b2; cursor: pointer; transition: color 0.2s; }
.prompt-hint:hover { color: #4f7fff; }
</style>