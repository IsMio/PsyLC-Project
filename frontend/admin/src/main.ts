import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import './style.css'
import { useThemeStore } from './store/modules/theme'

const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(Antd)

const themeStore = useThemeStore(pinia)
themeStore.initTheme()

app.mount('#app')
