import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import { createI18n } from "vue-i18n";

import App from "./App.vue";
import router from "./router";
import zhCN from "./locales/zh-CN.js";
import en from "./locales/en.js";

const i18n = createI18n({
  legacy: false,
  locale: "zh-CN",
  fallbackLocale: "zh-CN",
  messages: { "zh-CN": zhCN, en },
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.use(i18n);

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.mount("#app");
