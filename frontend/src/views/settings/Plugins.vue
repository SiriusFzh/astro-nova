<template>
  <div class="page">
    <div class="page-header">
      <h2>插件管理</h2>
      <el-button type="primary" size="small" @click="scan" :loading="scanning">扫描插件目录</el-button>
    </div>
    <p class="page-desc">管理 plugins_user 目录中的插件 — 激活的插件会注册工具供 AI 调用。</p>

    <el-empty v-if="loading && plugins.length === 0" description="加载中..." />

    <div v-for="p in plugins" :key="p.name" class="plugin-card">
      <div class="plugin-header">
        <div class="plugin-info">
          <span class="plugin-name">{{ p.name }}</span>
          <span class="plugin-version">v{{ p.version }}</span>
          <span class="plugin-desc">{{ p.description || "暂无描述" }}</span>
        </div>
        <div class="plugin-actions">
          <el-tag v-if="p.is_active" type="success" size="small" effect="dark">已激活</el-tag>
          <el-tag v-else type="info" size="small" effect="plain">未激活</el-tag>
          <el-button size="small" :disabled="!p.is_active" @click="reload(p.name)" :loading="loadingMap[p.name] === 'reload'">重载</el-button>
          <el-button size="small" :disabled="!p.is_active" @click="unload(p.name)" :loading="loadingMap[p.name] === 'unload'" type="danger" plain>卸载</el-button>
        </div>
      </div>
      <div class="plugin-meta" v-if="p.tool_count !== undefined">
        <el-tag size="small" type="info" effect="plain">{{ p.tool_count }} 个工具</el-tag>
        <el-tag v-if="p.author" size="small" type="warning" effect="plain">{{ p.author }}</el-tag>
      </div>
    </div>

    <el-empty v-if="!loading && plugins.length === 0" description="没有找到插件，请将插件放在 plugins_user 目录" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getPlugins, reloadPlugin, unloadPlugin, scanPlugins } from "@/api/client";
import { ElMessage } from "element-plus";

const plugins = ref<any[]>([]);
const loading = ref(false);
const scanning = ref(false);
const loadingMap = ref<Record<string, string>>({});

onMounted(async () => {
  await fetchList();
});

async function fetchList() {
  loading.value = true;
  try {
    const data = await getPlugins();
    plugins.value = data.plugins || [];
  } catch {
    ElMessage.error("获取插件列表失败");
  } finally {
    loading.value = false;
  }
}

async function scan() {
  scanning.value = true;
  try {
    const data = await scanPlugins();
    ElMessage.success(data.message);
    await fetchList();
  } catch {
    ElMessage.error("扫描失败");
  } finally {
    scanning.value = false;
  }
}

async function reload(name: string) {
  loadingMap.value[name] = "reload";
  try {
    const data = await reloadPlugin(name);
    ElMessage.success(data.message);
  } catch {
    ElMessage.error("重载失败");
  } finally {
    delete loadingMap.value[name];
  }
}

async function unload(name: string) {
  loadingMap.value[name] = "unload";
  try {
    const data = await unloadPlugin(name);
    ElMessage.success(data.message);
    await fetchList();
  } catch {
    ElMessage.error("卸载失败");
  } finally {
    delete loadingMap.value[name];
  }
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.plugin-card { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.plugin-header { display: flex; justify-content: space-between; align-items: flex-start; }
.plugin-info { display: flex; flex-direction: column; gap: 4px; }
.plugin-name { font-weight: 600; font-size: 15px; color: #303133; }
.plugin-version { font-size: 11px; color: #909399; margin-left: 6px; }
.plugin-desc { font-size: 12px; color: #909399; }
.plugin-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.plugin-meta { margin-top: 8px; display: flex; gap: 6px; }
</style>
