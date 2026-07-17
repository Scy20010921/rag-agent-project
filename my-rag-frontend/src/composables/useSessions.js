import { ref } from 'vue'

const API_BASE = 'http://localhost:8000/v1/chat'

export function useSessions() {
  const sessions = ref([])
  const currentSessionId = ref(null)

  const refreshSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`)
      const data = await res.json()
      sessions.value = data.sessions || []
    } catch (e) {
      console.error('获取会话列表失败:', e)
    }
  }

  const switchSession = (sessionId, onSwitch) => {
    if (sessionId === currentSessionId.value) return
    currentSessionId.value = sessionId
    if (onSwitch) onSwitch(sessionId)
  }

  const startNewChat = (onNew) => {
    currentSessionId.value = null
    if (onNew) onNew()
  }

  return { sessions, currentSessionId, refreshSessions, switchSession, startNewChat }
}