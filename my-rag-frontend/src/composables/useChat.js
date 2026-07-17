import { ref, reactive, computed, nextTick } from 'vue'

const WS_URL = 'ws://localhost:8000/v1/chat/ws'

export function useChat(question, deepThink, sessionsCtx, systemPrompt, getScrollEl) {
  const isLoading = ref(false)
  const messages = ref([])

  let ws = null
  let currentAssistantMsg = null

  const hasMessages = computed(() => messages.value.length > 0)
  const inputPlaceholder = computed(() =>
    deepThink.value ? '输入需要深度分析的问题...' : '询问助手是做什么的、是谁、能做什么等'
  )

  const scrollToBottom = () => {
    nextTick(() => {
      const el = getScrollEl ? getScrollEl() : null
      if (el) el.scrollTop = el.scrollHeight
    })
  }

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
        }else if (json.event === 'status') {
        const statusCard = reactive({ id: Date.now(), role: 'status', text: json.data })
        messages.value.push(statusCard)
        scrollToBottom()
        }else if (json.event === 'done') {
          isLoading.value = false
          currentAssistantMsg = null
          // ✅ 移除所有 role === 'status' 的消息
          messages.value = messages.value.filter(m => m.role !== 'status')
          sessionsCtx.refreshSessions?.()
        } else if (json.event === 'stopped') {
          isLoading.value = false
          currentAssistantMsg = null
        } else if (json.event === 'error') {
          console.error('WS error:', json.data)
          isLoading.value = false
          currentAssistantMsg = null
        } else if (json.event === 'session_created') {
          sessionsCtx.currentSessionId.value = json.data.session_id
          sessionsCtx.refreshSessions?.()
        } else if (json.event === 'history') {
          messages.value = json.data.map(m => ({ id: m.id, role: m.role, content: m.content }))
          scrollToBottom()
        } else if (json.event === 'tool_start') {
          const toolCard = reactive({
            id: Date.now(),
            role: 'tool',
            toolName: json.data.name,
            status: 'running',
            input: json.data.input,
            output: ''
          })
          messages.value.push(toolCard)
          scrollToBottom()
        } else if (json.event === 'tool_end') {
          for (let i = messages.value.length - 1; i >= 0; i--) {
            const m = messages.value[i]
            if (m.role === 'tool' && m.toolName === json.data.name && m.status === 'running') {
              m.status = 'done'
              m.output = json.data.output
              break
            }
          }
          scrollToBottom()
        }
      } catch (e) {}
    }

    ws.onclose = () => { isLoading.value = false; currentAssistantMsg = null }
    ws.onerror = () => { isLoading.value = false; currentAssistantMsg = null }
  }

  const disconnectWs = () => { if (ws) { ws.close(); ws = null } }

  const ws_send = (payload) => {
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

  const sendQuestion = () => {
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

    ws_send({
      type: 'chat',
      message: msg,
      session_id: sessionsCtx.currentSessionId?.value,
      model_type: modelType,
      system_prompt: systemPrompt?.value || ''
    })
  }

  const resetMessages = () => {
    messages.value = []
    currentAssistantMsg = null
    isLoading.value = false
  }

  return {
    isLoading, messages, currentAssistantMsg,
    hasMessages, inputPlaceholder,
    connectWs, disconnectWs, stopStream, sendQuestion, resetMessages, scrollToBottom,
    ws_send,
  }
}