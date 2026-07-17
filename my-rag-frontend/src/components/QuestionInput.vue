<template>
  <div class="question-card">
    <el-input
      :model-value="question"
      @update:model-value="$emit('update:question', $event)"
      type="textarea"
      :rows="2"
      :placeholder="inputPlaceholder"
      class="question-input"
      resize="none"
      @keydown.enter.prevent="$emit('send')"
    />
    <div class="question-toolbar">
      <div class="deep-think-toggle" :class="{ on: deepThink }" @click="$emit('update:deepThink', !deepThink)">
        <el-icon><MagicStick /></el-icon><span>深度思考</span><span v-if="deepThink" class="think-dot"></span>
      </div>
      <div v-if="isLoading" class="stop-btn" @click="$emit('stop')"><el-icon><VideoPause /></el-icon></div>
      <div v-else class="send-btn" :class="{ disabled: !question || !question.trim() }" @click="$emit('send')"><el-icon><Promotion /></el-icon></div>
    </div>
  </div>
</template>

<script setup>
import { MagicStick, Promotion, VideoPause } from '@element-plus/icons-vue'

defineProps({
  question: String,
  deepThink: Boolean,
  isLoading: Boolean,
  inputPlaceholder: String,
})

defineEmits(['send', 'stop', 'update:deepThink', 'update:question'])
</script>

<style scoped>
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
</style>