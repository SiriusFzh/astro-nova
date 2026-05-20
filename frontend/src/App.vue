<template>
  <div class="app-shell">
    <!-- Custom Title Bar -->
    <div class="titlebar" data-tauri-drag-region>
      <div class="titlebar-left">
        <img src="/app-icon.png" class="titlebar-icon" />
        <span class="titlebar-title">AstroNova</span>
      </div>
      <div class="titlebar-right">
        <div class="titlebar-btn" @click="minimize" title="最小化">
          <el-icon :size="14"><Minus /></el-icon>
        </div>
        <div class="titlebar-btn" @click="toggleMaximize" :title="isMaximized ? '还原' : '最大化'">
          <el-icon :size="12"><CopyDocument v-if="isMaximized" /><FullScreen v-else /></el-icon>
        </div>
        <div class="titlebar-btn titlebar-close" @click="closeWindow" title="关闭">
          <el-icon :size="14"><Close /></el-icon>
        </div>
      </div>
    </div>

    <!-- Main layout -->
    <el-container class="app-container">
      <el-aside width="200px" class="app-sidebar">
        <div class="sidebar-header">
          <img src="/app-icon.png" class="sidebar-icon" />
          <span class="sidebar-title">AstroNova</span>
        </div>
        <el-menu
          :default-active="currentRoute"
          :router="true"
          class="sidebar-menu"
          background-color="#1a1a2e"
          text-color="#b0b0c0"
          active-text-color="#fff"
        >
          <el-menu-item index="/chat">
            <el-icon><ChatLineSquare /></el-icon>
            <span>{{ $t('nav.chat') }}</span>
            <span v-if="taskStore.badge('/chat')" class="menu-badge">{{ taskStore.badge('/chat') }}</span>
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <span>{{ $t('nav.search') }}</span>
          </el-menu-item>
          <el-menu-item index="/papers">
            <el-icon><Notebook /></el-icon>
            <span>{{ $t('nav.papers') }}</span>
            <span v-if="taskStore.badge('/papers')" class="menu-badge">{{ taskStore.badge('/papers') }}</span>
          </el-menu-item>
          <el-menu-item index="/notes">
            <el-icon><Edit /></el-icon>
            <span>{{ $t('nav.notes') }}</span>
            <span v-if="taskStore.badge('/notes')" class="menu-badge">{{ taskStore.badge('/notes') }}</span>
          </el-menu-item>
          <el-menu-item index="/paper-viewer">
            <el-icon><View /></el-icon>
            <span>论文阅读</span>
          </el-menu-item>
          <el-menu-item index="/digest">
            <el-icon><DataBoard /></el-icon>
            <span>每日 Digest</span>
            <span v-if="taskStore.badge('/digest')" class="menu-badge">{{ taskStore.badge('/digest') }}</span>
          </el-menu-item>
          <el-menu-item index="/figures">
            <el-icon><Picture /></el-icon>
            <span>{{ $t('nav.figures') }}</span>
            <span v-if="taskStore.badge('/figures')" class="menu-badge">{{ taskStore.badge('/figures') }}</span>
          </el-menu-item>
          <el-menu-item index="/writing">
            <el-icon><Document /></el-icon>
            <span>{{ $t('nav.writing') }}</span>
            <span v-if="taskStore.badge('/writing')" class="menu-badge">{{ taskStore.badge('/writing') }}</span>
          </el-menu-item>
          <el-menu-item index="/ppt">
            <el-icon><Monitor /></el-icon>
            <span>{{ $t('nav.ppt') }}</span>
            <span v-if="taskStore.badge('/ppt')" class="menu-badge">{{ taskStore.badge('/ppt') }}</span>
          </el-menu-item>
          <el-sub-menu index="settings">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>{{ $t('nav.settings') }}</span>
            </template>
            <el-menu-item index="/settings/general">{{ $t('nav.general') }}</el-menu-item>
            <el-menu-item index="/settings/providers">{{ $t('nav.providers') }}</el-menu-item>
            <el-menu-item index="/settings/knowledge">{{ $t('nav.knowledge') }}</el-menu-item>
            <el-menu-item index="/settings/skills">{{ $t('nav.skills') }}</el-menu-item>
            <el-menu-item index="/settings/plugins">{{ $t('nav.plugins') }}</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { getSettings } from "@/api/client";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { invoke } from "@tauri-apps/api/core";
import { ElMessage, ElMessageBox } from "element-plus";
import { Minus, CopyDocument, FullScreen, Close, View, DataBoard } from "@element-plus/icons-vue";
import { useTaskStore } from "@/stores/tasks";

const route = useRoute();
const router = useRouter();
const currentRoute = computed(() => route.path);
const { locale } = useI18n();
const isMaximized = ref(false);

const taskStore = useTaskStore();

const appWindow = getCurrentWindow();

function applyTheme(theme: string) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

async function minimize() {
  await appWindow.minimize();
}

async function toggleMaximize() {
  await appWindow.toggleMaximize();
}

async function closeWindow() {
  // 触发 Tauri 关闭请求，由 onCloseRequested 拦截处理
  await appWindow.close();
}

async function showCloseDialog() {
  try {
    await ElMessageBox.confirm(
      '后端进程将停止运行。',
      '关闭 AstroNova',
      {
        confirmButtonText: '最小化到托盘',
        cancelButtonText: '直接退出',
        close: false,
        type: 'info',
      }
    );
    // 最小化到托盘
    await appWindow.hide();
  } catch (action: any) {
    if (action === 'cancel') {
      // 直接退出
      try { await invoke("confirm_quit"); } catch {}
    }
    // action === 'close' → 什么也不做
  }
}

async function checkMaximized() {
  isMaximized.value = await appWindow.isMaximized();
}

let unlistenResize: (() => void) | null = null;

async function checkProviders() {
  try {
    const providers = await (await fetch("http://127.0.0.1:8615/api/providers")).json();
    if (!providers || providers.length === 0) {
      ElMessage.warning("尚未配置 AI 模型，请先添加 Provider", { duration: 6000 });
      // 3 秒后引导去设置页
      setTimeout(() => {
        router.push("/settings/providers");
      }, 3000);
    }
  } catch { /* backend not ready */ }
}

onMounted(async () => {
  await checkMaximized();
  unlistenResize = await appWindow.onResized(checkMaximized);

  // 拦截关闭事件（X 按钮 / Alt+F4）
  appWindow.onCloseRequested(async (event) => {
    event.preventDefault();
    await showCloseDialog();
  });

  // 全局任务通知轮询
  taskStore.startPolling();
  taskStore.onRouteChanged(route.path);
  router.afterEach((to) => {
    taskStore.onRouteChanged(to.path);
  });

  try {
    const cfg = await getSettings();
    applyTheme(cfg.theme);
    if (cfg.language === "en") locale.value = "en";
  } catch { /* use defaults */ }

  // 检查是否有 Provider 配置（首次运行引导）
  await checkProviders();
});

onUnmounted(() => {
  if (unlistenResize) unlistenResize();
  taskStore.stopPolling();
});
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: -apple-system, 'Segoe UI', sans-serif; overflow: hidden; }

/* Title Bar */
.titlebar {
  height: 32px;
  background: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: space-between;
  user-select: none;
  -webkit-user-select: none;
  flex-shrink: 0;
}
.titlebar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  height: 100%;
}
.titlebar-icon {
  width: 18px;
  height: 18px;
  border-radius: 4px;
}
.titlebar-title {
  font-size: 13px;
  font-weight: 600;
  color: #c0c0d0;
  letter-spacing: 0.5px;
}
.titlebar-right {
  display: flex;
  height: 100%;
}
.titlebar-btn {
  width: 46px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  cursor: pointer;
  transition: background 0.15s;
}
.titlebar-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #e0e0e0;
}
.titlebar-close:hover {
  background: #e81123;
  color: #fff;
}

.app-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-container { flex: 1; min-height: 0; }
.app-sidebar { background: #1a1a2e; color: #fff; }
.sidebar-header {
  display: flex; align-items: center; gap: 8px; padding: 16px;
  font-size: 16px; font-weight: bold; color: #fff; border-bottom: 1px solid #16213e;
}
.sidebar-icon {
  width: 22px;
  height: 22px;
  border-radius: 4px;
}
.sidebar-title { letter-spacing: 0.5px; }
.sidebar-menu { border-right: none; }
.sidebar-menu :deep(.el-menu-item) { position: relative; }
.app-main { background: #f5f7fa; overflow-y: auto; padding: 0; display: flex; flex-direction: column; width: 100%; min-width: 0; }
.app-main > * { flex: 1; width: 100%; }

/* 通知角标 */
.menu-badge {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: #f56c6c;
  color: #fff;
  border-radius: 10px;
  padding: 0 6px;
  font-size: 11px;
  line-height: 18px;
  min-width: 18px;
  text-align: center;
  font-weight: 600;
  box-shadow: 0 0 0 2px #1a1a2e;
}

/* 深色主题 */
[data-theme="dark"] .app-main { background: #1a1a2e; color: #e0e0e0; }
[data-theme="dark"] .el-card { background: #16213e; color: #e0e0e0; border-color: #0f3460; }
[data-theme="dark"] .el-form-item__label { color: #b0b0c0; }
[data-theme="dark"] .el-input__wrapper { background: #0f3460; box-shadow: 0 0 0 1px #1a3a6a inset; }
[data-theme="dark"] .el-input__inner { color: #e0e0e0; }
[data-theme="dark"] .chat-input { background: #16213e; border-top-color: #0f3460; }
[data-theme="dark"] .msg.assistant .msg-content { background: #16213e; color: #e0e0e0; border-color: #0f3460; }
[data-theme="dark"] .chat-empty h2 { color: #e0e0e0; }
[data-theme="dark"] .chat-empty p { color: #b0b0c0; }
[data-theme="dark"] .page-header h2 { color: #e0e0e0; }
</style>
