<template>
  <el-aside width="270px" class="sidebar">
    <div class="logo-area">
      <div class="logo-icon"><el-icon><ChatDotRound /></el-icon></div>
      <div class="logo-text">
        <span class="logo-title">RAG 智能问答</span>
        <span class="logo-sub">Powered by AI</span>
      </div>
    </div>

    <div class="quick-start-card">
      <div v-if="!hasMessages" class="quick-start-top">
        <span class="quick-start-label">快速开始</span>
        <span class="quick-start-badge">新内容</span>
      </div>
      <div class="new-chat-row" @click="$emit('newChat')">
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
          @click="$emit('switchSession', s.id)"
        >
          {{ s.title }}
        </li>
        <li v-if="sessions.length === 0" class="history-item-empty">暂无历史对话</li>
      </ul>
    </div>

    <!-- 知识库管理 -->
    <div class="doc-section">
      <div class="doc-header" @click="docOpen = !docOpen">
        <span class="doc-label">📚 知识库</span>
        <el-icon class="doc-arrow" :class="{ open: docOpen }"><ArrowRight /></el-icon>
      </div>
      <div v-show="docOpen" class="doc-body">
        <el-upload
          ref="uploadRef"
          :action="`${API_BASE}/documents/upload`"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :show-file-list="false"
          accept=".txt,.md,.pdf"
        >
          <div class="upload-btn">
            <el-icon><UploadFilled /></el-icon>
            <span>上传文档</span>
          </div>
        </el-upload>
        <ul class="doc-list">
          <li v-for="d in documents" :key="d.id" class="doc-item">
            <span class="doc-name" :title="d.filename">{{ d.filename }}</span>
            <span class="doc-status" :class="d.status">{{ d.status === 'ready' ? `✓ ${d.chunk_count}段` : d.status }}</span>
            <el-icon class="doc-del" @click.stop="handleDeleteDoc(d.id)"><Delete /></el-icon>
          </li>
          <li v-if="documents.length === 0" class="doc-empty">暂无文档</li>
        </ul>
      </div>
    </div>

    <div class="user-info">
      <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a53f6f0f6dpng.png" />
      <span class="user-name">admin</span>
    </div>
  </el-aside>
</template>

<script setup>
import { ref } from 'vue'
import { ChatDotRound, Plus, ArrowRight, UploadFilled, Delete } from '@element-plus/icons-vue'

const API_BASE = 'http://localhost:8000/v1'

defineProps({
  hasMessages: Boolean,
  sessions: { type: Array, default: () => [] },
  currentSessionId: { type: String, default: null },
  documents: { type: Array, default: () => [] },
})

const emit = defineEmits(['newChat', 'switchSession', 'uploadDone', 'deleteDoc'])

const docOpen = ref(false)
const uploadRef = ref(null)

const handleUploadSuccess = (response) => {
  emit('uploadDone')
}

const handleUploadError = (err) => {
  console.error('上传失败:', err)
}

const handleDeleteDoc = (docId) => {
  emit('deleteDoc', docId)
}
</script>

<style scoped>
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
.history-section { flex: 1; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #d5dae2 transparent; min-height: 0; }
.history-section::-webkit-scrollbar { width: 5px; }
.history-section::-webkit-scrollbar-track { background: transparent; }
.history-section::-webkit-scrollbar-thumb { background: #e0e3e9; border-radius: 3px; }
.history-label { font-size: 12px; color: #b0b8c4; padding: 4px 6px 8px 6px; }
.history-list { list-style: none; margin: 0; padding: 0; }
.history-item { font-size: 13.5px; color: #4e5969; padding: 9px 8px; border-radius: 8px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: background 0.15s; }
.history-item:hover { background: #f5f6f9; }
.history-item.active { background: #eef2ff; color: #4f7fff; font-weight: 500; }
.history-item-empty { font-size: 12.5px; color: #b0b8c4; padding: 9px 8px; }

/* 知识库 */
.doc-section { border-top: 1px solid #f0f2f5; padding-top: 10px; }
.doc-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 6px 8px 6px; cursor: pointer; }
.doc-label { font-size: 12px; color: #b0b8c4; }
.doc-arrow { font-size: 12px; color: #b0b8c4; transition: transform 0.2s; }
.doc-arrow.open { transform: rotate(90deg); }
.doc-body { padding: 0 4px; }
.upload-btn { display: flex; align-items: center; gap: 6px; padding: 8px 10px; border: 1px dashed #c7d2fe; border-radius: 8px; cursor: pointer; font-size: 12.5px; color: #4f7fff; transition: background 0.15s; }
.upload-btn:hover { background: #eef2ff; }
.doc-list { list-style: none; margin: 8px 0 0 0; padding: 0; max-height: 160px; overflow-y: auto; }
.doc-item { display: flex; align-items: center; gap: 6px; padding: 6px 6px; border-radius: 6px; font-size: 12px; }
.doc-item:hover { background: #f5f6f9; }
.doc-name { flex: 1; color: #4e5969; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-status { font-size: 11px; color: #b0b8c4; }
.doc-status.ready { color: #22c55e; }
.doc-status.error { color: #f56c6c; }
.doc-del { font-size: 13px; color: #c2c8d1; cursor: pointer; }
.doc-del:hover { color: #f56c6c; }
.doc-empty { font-size: 12px; color: #b0b8c4; padding: 6px; }

.user-info { display: flex; align-items: center; gap: 10px; padding: 14px 6px 0 6px; border-top: 1px solid #f0f2f5; font-size: 14px; color: #303133; margin-top: 10px; }
.user-name { flex: 1; }
</style>