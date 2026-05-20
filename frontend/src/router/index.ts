import { createRouter, createWebHashHistory } from "vue-router";
import Chat from "@/views/Chat.vue";
import Providers from "@/views/settings/Providers.vue";
import Skills from "@/views/settings/Skills.vue";
import Plugins from "@/views/settings/Plugins.vue";
import General from "@/views/settings/General.vue";
import Search from "@/views/Search.vue";
import Notes from "@/views/Notes.vue";
import Papers from "@/views/Papers.vue";
import Figures from "@/views/Figures.vue";
import Writing from "@/views/Writing.vue";
import PPT from "@/views/PPT.vue";
import Knowledge from "@/views/Knowledge.vue";
import Digest from "@/views/Digest.vue";
import PaperViewer from "@/views/PaperViewer.vue";

const routes = [
  { path: "/", redirect: "/chat" },
  { path: "/chat", name: "Chat", component: Chat, meta: { title: "对话", icon: "ChatLineSquare" } },
  { path: "/search", name: "Search", component: Search, meta: { title: "文献搜索", icon: "Search" } },
  { path: "/papers", name: "Papers", component: Papers, meta: { title: "论文库", icon: "Notebook" } },
  { path: "/notes", name: "Notes", component: Notes, meta: { title: "笔记", icon: "Edit" } },
  { path: "/paper-viewer", name: "PaperViewer", component: PaperViewer, meta: { title: "论文阅读", icon: "View" } },
  { path: "/digest", name: "Digest", component: Digest, meta: { title: "每日 Digest", icon: "DataBoard" } },
  { path: "/figures", name: "Figures", component: Figures, meta: { title: "科研制图", icon: "Picture" } },
  { path: "/writing", name: "Writing", component: Writing, meta: { title: "论文写作", icon: "Document" } },
  { path: "/ppt", name: "PPT", component: PPT, meta: { title: "PPT 生成", icon: "Monitor" } },
  {
    path: "/settings",
    redirect: "/settings/general",
    meta: { title: "设置", icon: "Setting" },
    children: [
      { path: "general", name: "General", component: General, meta: { title: "通用" } },
      { path: "providers", name: "Providers", component: Providers, meta: { title: "模型配置" } },
      { path: "knowledge", name: "Knowledge", component: Knowledge, meta: { title: "知识库" } },
      { path: "skills", name: "Skills", component: Skills, meta: { title: "技能" } },
      { path: "plugins", name: "Plugins", component: Plugins, meta: { title: "插件" } },
    ],
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
