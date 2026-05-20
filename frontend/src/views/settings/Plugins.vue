<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('settings.plugins.title') }}</h2>
      <el-button type="primary" size="small" @click="scan" :loading="scanning">{{ $t('settings.plugins.scan') }}</el-button>
    </div>
    <p class="page-desc">{{ $t('settings.plugins.desc') }}</p>

    <el-empty v-if="loading && plugins.length === 0" :description="$t('settings.plugins.loading')" />

    <div v-for="p in plugins" :key="p.name" class="plugin-card">
      <div class="plugin-header">
        <div class="plugin-info">
          <span class="plugin-name">{{ p.name }}</span>
          <span class="plugin-version">v{{ p.version }}</span>
          <span class="plugin-desc">{{ p.description || $t('settings.plugins.noDesc') }}</span>
        </div>
        <div class="plugin-actions">
          <el-tag v-if="p.is_active" type="success" size="small" effect="dark">{{ $t('settings.plugins.active') }}</el-tag>
          <el-tag v-else type="info" size="small" effect="plain">{{ $t('settings.plugins.inactive') }}</el-tag>
          <el-button size="small" :disabled="!p.is_active" @click="reload(p.name)" :loading="loadingMap[p.name] === 'reload'">{{ $t('settings.plugins.reload') }}</el-button>
          <el-button size="small" :disabled="!p.is_active" @click="unload(p.name)" :loading="loadingMap[p.name] === 'unload'" type="danger" plain>{{ $t('settings.plugins.unload') }}</el-button>
        </div>
      </div>
      <div class="plugin-meta" v-if="p.tool_count !== undefined">
        <el-tag size="small" type="info" effect="plain">{{ p.tool_count }} {{ $t('settings.plugins.toolCount') }}</el-tag>
        <el-tag v-if="p.author" size="small" type="warning" effect="plain">{{ p.author }}</el-tag>
      </div>
    </div>

    <el-empty v-if="!loading && plugins.length === 0" :description="$t('settings.plugins.empty')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { getPlugins, reloadPlugin, unloadPlugin, scanPlugins } from "@/api/client";
import { ElMessage } from "element-plus";

const { t } = useI18n();
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
    ElMessage.error(t('settings.plugins.fetchFailed'));
  } finally {
    loading.value = false;
  }
}

async function scan() {
  scanning.value = true;
  try {
    const data = await scanPlugins();
    ElMessage.success(t('settings.plugins.scanSuccess'));
    await fetchList();
  } catch {
    ElMessage.error(t('settings.plugins.scanFailed'));
  } finally {
    scanning.value = false;
  }
}

async function reload(name: string) {
  loadingMap.value[name] = "reload";
  try {
    const data = await reloadPlugin(name);
    ElMessage.success(t('settings.plugins.reloadSuccess'));
  } catch {
    ElMessage.error(t('settings.plugins.reloadFailed'));
  } finally {
    delete loadingMap.value[name];
  }
}

async function unload(name: string) {
  loadingMap.value[name] = "unload";
  try {
    const data = await unloadPlugin(name);
    ElMessage.success(t('settings.plugins.unloadSuccess'));
    await fetchList();
  } catch {
    ElMessage.error(t('settings.plugins.unloadFailed'));
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
