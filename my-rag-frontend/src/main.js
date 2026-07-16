import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

// 1. 引入 Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 2. 创建应用
const app = createApp(App)

// 3. 使用 Element Plus
app.use(ElementPlus)

app.mount('#app')