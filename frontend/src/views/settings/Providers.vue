<template>
  <div class="page">
    <div class="page-header">
      <h2>模型配置</h2>
      <el-button type="primary" @click="dialogVisible = true">
        <el-icon><Plus /></el-icon> 添加 Provider
      </el-button>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && providers.length === 0" description="还没有配置 LLM Provider，点击上方按钮添加" />

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
            {{ p.is_active ? '启用' : '停用' }}
          </el-tag>
          <el-tag type="warning" size="small" v-if="p.task_route !== 'all'">
            {{ taskRouteLabel(p.task_route) }}
          </el-tag>
          <el-button text type="danger" :icon="Delete" @click="handleDelete(p.id)" />
        </div>
      </div>
      <div class="provider-meta">
        <span v-if="p.website">官网: {{ p.website }}</span>
        <span v-if="p.api_base">API: {{ p.api_base }}</span>
      </div>
    </el-card>

    <!-- 添加 Provider 对话框 -->
    <el-dialog v-model="dialogVisible" title="添加 Provider" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="供应商名称" required>
          <el-input v-model="form.display_name" placeholder="例: OpenAI" />
        </el-form-item>
        <el-form-item label="供应商类型" required>
          <el-select v-model="form.provider_type" style="width:100%">
            <el-option label="OpenAI 兼容" value="openai" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Anthropic Claude" value="anthropic" />
            <el-option label="Ollama 本地" value="ollama" />
          </el-select>
        </el-form-item>
        <el-form-item label="官网链接">
          <el-input v-model="form.website" placeholder="例: https://openai.com" />
        </el-form-item>
        <el-form-item label="模型型号" required>
          <el-input v-model="form.model" placeholder="例: gpt-4o / claude-sonnet-4-20250514" />
        </el-form-item>
        <el-form-item label="API 地址">
          <el-input v-model="form.api_base" placeholder="例: https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="任务路由">
          <el-select v-model="form.task_route" style="width:100%">
            <el-option label="所有任务 (默认)" value="all" />
            <el-option label="对话" value="chat" />
            <el-option label="文献搜索" value="search" />
            <el-option label="论文精读" value="read" />
            <el-option label="笔记/写作" value="write" />
            <el-option label="代码/制图" value="code" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="saving">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getProviders, createProvider, deleteProvider } from "@/api/client";
import { Plus, Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

const providers = ref<any[]>([]);
const loading = ref(false);
const saving = ref(false);
const dialogVisible = ref(false);

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
  const map: Record<string, string> = { all: "通用", chat: "对话", search: "搜索", read: "精读", write: "写作", code: "代码" };
  return map[route] || route;
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
    ElMessage.warning("请填写必填字段");
    return;
  }
  form.value.name = `${form.value.provider_type}-${Date.now()}`;
  saving.value = true;
  try {
    await createProvider(form.value);
    ElMessage.success("添加成功");
    dialogVisible.value = false;
    form.value = { display_name: "", provider_type: "openai", website: "", model: "", api_base: "", api_key: "", task_route: "all", name: "" };
    await loadProviders();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "添加失败");
  } finally {
    saving.value = false;
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm("确定删除这个 Provider？", "确认");
    await deleteProvider(id);
    ElMessage.success("已删除");
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
