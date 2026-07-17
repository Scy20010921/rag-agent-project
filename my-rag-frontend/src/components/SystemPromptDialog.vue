<template>
  <el-dialog
    v-model="visible"
    title="系统提示词设置"
    width="580px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-input
      v-model="localPrompt"
      type="textarea"
      :rows="6"
      placeholder="例如：你是一个企业知识库助手，回答要简洁专业，使用中文。"
      resize="none"
    />
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  systemPrompt: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'save'])

const visible = ref(props.modelValue)
const localPrompt = ref(props.systemPrompt)

watch(() => props.modelValue, (v) => { visible.value = v })
watch(() => props.systemPrompt, (v) => { localPrompt.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const save = () => {
  emit('save', localPrompt.value)
  visible.value = false
}
</script>