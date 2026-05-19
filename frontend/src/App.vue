<template>
  <el-container class="app-container">
    <el-aside width="200px" class="app-sidebar">
      <div class="sidebar-header">
        <el-icon :size="24" color="#1a237e"><Telescope /></el-icon>
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
          <span>对话</span>
        </el-menu-item>
        <el-menu-item index="/search">
          <el-icon><Search /></el-icon>
          <span>文献搜索</span>
        </el-menu-item>
        <el-menu-item index="/papers">
          <el-icon><Notebook /></el-icon>
          <span>论文库</span>
        </el-menu-item>
        <el-menu-item index="/notes">
          <el-icon><Edit /></el-icon>
          <span>笔记</span>
        </el-menu-item>
        <el-menu-item index="/figures">
          <el-icon><Picture /></el-icon>
          <span>科研制图</span>
        </el-menu-item>
        <el-menu-item index="/writing">
          <el-icon><Document /></el-icon>
          <span>论文写作</span>
        </el-menu-item>
        <el-menu-item index="/ppt">
          <el-icon><Monitor /></el-icon>
          <span>PPT 生成</span>
        </el-menu-item>
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </template>
          <el-menu-item index="/settings/general">通用</el-menu-item>
          <el-menu-item index="/settings/providers">模型配置</el-menu-item>
          <el-menu-item index="/settings/knowledge">知识库</el-menu-item>
          <el-menu-item index="/settings/skills">技能</el-menu-item>
          <el-menu-item index="/settings/plugins">插件</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container class="app-main">
      <router-view />
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
const route = useRoute();
const currentRoute = computed(() => route.path);
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: -apple-system, 'Segoe UI', sans-serif; }

.app-container { height: 100vh; }
.app-sidebar { background: #1a1a2e; color: #fff; }
.sidebar-header {
  display: flex; align-items: center; gap: 8px; padding: 20px 16px;
  font-size: 18px; font-weight: bold; color: #fff; border-bottom: 1px solid #16213e;
}
.sidebar-menu { border-right: none; }
.app-main { background: #f5f7fa; overflow-y: auto; }
</style>
