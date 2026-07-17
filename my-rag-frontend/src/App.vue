<template>
  <ChatView />
</template>

<script setup>
import ChatView from './views/ChatView.vue'
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; width: 100%; }
#app {
  text-align: left;   /* 或 right / initial / unset */
}
</style>