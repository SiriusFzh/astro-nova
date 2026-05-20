<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('settings.providers.title') }}</h2>
      <el-button type="primary" @click="dialogVisible = true">
        <el-icon><Plus /></el-icon> {{ $t('settings.providers.add') }}
      </el-button>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && providers.length === 0" :description="$t('settings.providers.empty')" />

    <!-- Provider 列表 -->
    <el-card v-for="p in providers" :key="p.id" class="provider-card" shadow="hover">
      <div class="provider-info">
        <div class="provider-left">
          <el-tag :type="getProviderTag(p.provider_type)" size="small">{{ p.provider_type }}</el-tag>
          <span class="provider-name">{{ p.display_name }}</span>
          <span class="provider-model">{{ p.model }}</span>
        </div>
        <div class="provider-right">
          <el-tag :type="p.is_active ? 'success' : 'info'" size="small" effect="plain">
            {{ p.is_active ? $t('settings.providers.active') : $t('settings.providers.inactive') }}
          </el-tag>
          <el-tag type="warning" size="small" v-if="p.task_route !== 'all'">
            {{ taskRouteLabel(p.task_route) }}
          </el-tag>
          <el-button text type="danger" :icon="Delete" @click="handleDelete(p.id)" />
        </div>
      </div>
      <div class="provider-meta">
        <span v-if="p.website">{{ $t('settings.providers.website') }}: {{ p.website }}</span>
        <span v-if="p.api_base">API: {{ p.api_base }}</span>
      </div>
    </el-card>

    <!-- 添加 Provider 对话框 -->
    <el-dialog v-model="dialogVisible" :title="$t('settings.providers.addTitle')" width="520px">
      <el-form :model="form" :label-width="formLabelWidth">
        <el-form-item :label="$t('settings.providers.fields.name')" required>
          <el-input v-model="form.display_name" :placeholder="'例: OpenAI / Example: OpenAI'" />
        </el-form-item>
        <el-form-item :label="$t('settings.providers.fields.type')" required>
          <el-select v-model="form.provider_type" style="width:100%">
            <el-option :label="$t('settings.providers.types.openai')" value="openai" />
            <el-option :label="$t('settings.providers.types.deepseek')" value="deepseek" />
            <el-option :label="$t('settings.providers.types.anthropic')" value="anthropic" />
            <el-option :label="$t('settings.providers.types.ollama')" value="ollama" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('settings.providers.fields.website')">
          <el-input v-model="form.website" :placeholder="'例: https://openai.com'" />
        </el-form-item>
        <el-form-item :label="$t('settings.providers.fields.model')" required>
          <el-input v-model="form.model" :placeholder="'例: gpt-4o / claude-sonnet-4-20250514'" />
        </el-form-item>
        <el-form-item :label="$t('settings.providers.fields.apiBase')">
          <el-input v-model="form.api_base" :placeholder="'例: https://api.openai.com/v1'" />
        </el-form-item>
        <el-form-item :label="$t('settings.providers.fields.apiKey')" required>
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item :label="$t('settings.providers.fields.taskRoute')">
          <el-select v-model="form.task_route" style="width:100%">
            <el-option :label="$t('settings.providers.routes.all')" value="all" />
            <el-option :label="$t('settings.providers.routes.chat')" value="chat" />
            <el-option :label="$t('settings.providers.routes.search')" value="search" />
            <el-option :label="$t('settings.providers.routes.read')" value="read" />
            <el-option :label="$t('settings.providers.routes.write')" value="write" />
            <el-option :label="$t('settings.providers.routes.code')" value="code" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('settings.providers.cancel') || $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAdd" :loading="saving">{{ $t('settings.providers.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { getProviders, createProvider, deleteProvider } from "@/api/client";
import { Plus, Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

const { t } = useI18n();
const providers = ref<any[]>([]);
const loading = ref(false);
const saving = ref(false);
const dialogVisible = ref(false);
const formLabelWidth = computed(() => t('settings.providers.fields.name').length > 6 ? '120px' : '100px');

const form = ref({
  display_name: "",
  provider_type: "openai",
  website: "",
  model: "",
  api_base: "",
  api_key: "",
  task_route: "all",
  name: "",
});

function getProviderTag(type: string) {
  const map: Record<string, string> = { openai: "", deepseek: "success", anthropic: "warning", ollama: "info" };
  return map[type] || "";
}

function taskRouteLabel(route: string) {
  const labels: Record<string, string> = {
    all: t('settings.providers.routes.all'),
    chat: t('settings.providers.routes.chat'),
    search: t('settings.providers.routes.search'),
    read: t('settings.providers.routes.read'),
    write: t('settings.providers.routes.write'),
    code: t('settings.providers.routes.code'),
  };
  return labels[route] || route;
}

async function loadProviders() {
  loading.value = true;
  try {
    providers.value = await getProviders();
  } finally {
    loading.value = false;
  }
}

async function handleAdd() {
  if (!form.value.display_name || !form.value.model || !form.value.api_key) {
    ElMessage.warning(t('settings.providers.pleaseFillRequired'));
    return;
  }
  form.value.name = `${form.value.provider_type}-${Date.now()}`;
  saving.value = true;
  try {
    await createProvider(form.value);
    ElMessage.success(t('settings.providers.added'));
    dialogVisible.value = false;
    form.value = { display_name: "", provider_type: "openai", website: "", model: "", api_base: "", api_key: "", task_route: "all", name: "" };
    await loadProviders();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('settings.providers.addFailed'));
  } finally {
    saving.value = false;
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm(t('settings.providers.deleteConfirm'), t('settings.providers.deleteTitle'));
    await deleteProvider(id);
    ElMessage.success(t('settings.providers.deleted'));
    await loadProviders();
  } catch {}
}

onMounted(loadProviders);
</script>

<style scoped>
.page { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.provider-card { margin-bottom: 12px; }
.provider-info { display: flex; justify-content: space-between; align-items: center; }
.provider-left { display: flex; align-items: center; gap: 12px; }
.provider-name { font-weight: 600; font-size: 15px; color: #303133; }
.provider-model { color: #909399; font-size: 13px; font-family: monospace; }
.provider-right { display: flex; align-items: center; gap: 8px; }
.provider-meta { margin-top: 8px; font-size: 12px; color: #909399; display: flex; gap: 16px; }
</style>
