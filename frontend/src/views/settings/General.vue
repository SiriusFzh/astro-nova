<template>
  <div class="page">
    <div class="page-header"><h2>{{ $t('settings.general.title') }}</h2></div>
    <p class="page-desc">{{ $t('settings.general.desc') }}</p>

    <div v-if="loading" class="loading-wrap"><el-icon class="is-loading" :size="24"><Loading /></el-icon> {{ $t('common.loading') }}</div>

    <el-form v-else label-position="top" class="settings-form">
      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">{{ $t('settings.general.interface') }}</span></template>
        <el-form-item :label="$t('settings.general.language')">
          <el-radio-group v-model="cfg.language" @change="switchLanguage">
            <el-radio value="zh-CN">简体中文</el-radio>
            <el-radio value="en">English</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="$t('settings.general.theme')">
          <el-radio-group v-model="cfg.theme">
            <el-radio value="light">{{ $t('settings.general.light') }}</el-radio>
            <el-radio value="dark">{{ $t('settings.general.dark') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-card>

      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">{{ $t('settings.general.llm') }}</span></template>
        <el-form-item :label="$t('settings.general.defaultTask')">
          <el-select v-model="cfg.default_task_type" style="width:240px">
            <el-option label="通用对话 (chat)" value="chat" />
            <el-option label="文献搜索与精读 (search/read)" value="search" />
            <el-option label="笔记生成 (write)" value="write" />
            <el-option label="制图代码 (code)" value="code" />
          </el-select>
          <p class="form-tip">{{ $t('settings.general.taskTip') }}</p>
        </el-form-item>
        <el-form-item :label="$t('settings.general.maxTokens')">
          <el-input-number v-model="cfg.max_tokens" :min="512" :max="32768" :step="512" />
          <p class="form-tip">{{ $t('settings.general.tokenTip') }}</p>
        </el-form-item>
        <el-form-item :label="$t('settings.general.temperature')">
          <el-slider v-model="cfg.temperature" :min="0" :max="2" :step="0.1" style="width:300px" />
          <p class="form-tip">{{ $t('settings.general.tempTip') }}</p>
        </el-form-item>
      </el-card>

      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">{{ $t('settings.general.service') }}</span></template>
        <el-form-item :label="$t('settings.general.port')">
          <el-input-number v-model="cfg.port" :min="1024" :max="65535" />
          <p class="form-tip">{{ $t('settings.general.portTip') }}</p>
        </el-form-item>
        <el-form-item :label="$t('settings.general.logLevel')">
          <el-select v-model="cfg.log_level" style="width:180px">
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
        </el-form-item>
      </el-card>

      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">{{ $t('settings.general.storage') }}</span></template>
        <el-form-item :label="$t('settings.general.dataDir')">
          <el-input v-model="cfg.data_dir" placeholder="~/.astro-nova" />
          <p class="form-tip">{{ $t('settings.general.dataDirTip') }}</p>
        </el-form-item>
        <el-form-item label="笔记输出目录">
          <el-input v-model="cfg.notes_dir" placeholder="留空则使用默认位置" />
          <p class="form-tip">
            当前: <code>{{ currentOutputDir || '未设置' }}</code> · 留空自动使用安装目录旁的 notes/
          </p>
        </el-form-item>
        <el-form-item :label="$t('settings.general.knowledgeStore')">
          <el-input v-model="cfg.knowledge_store" placeholder="default" />
        </el-form-item>
      </el-card>

      <div class="form-actions">
        <el-button type="primary" @click="saveSettings" :loading="saving">{{ $t('settings.general.save') }}</el-button>
        <el-button @click="resetSettings">{{ $t('settings.general.reset') }}</el-button>
        <span v-if="saved" class="save-hint"><el-icon color="#67c23a"><SuccessFilled /></el-icon> {{ $t('settings.general.saved') }}</span>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { getSettings, updateSettings, getNovaForgeOutputDir } from "@/api/client";
import { ElMessage } from "element-plus";
import { Loading, SuccessFilled } from "@element-plus/icons-vue";

const { locale } = useI18n();
const loading = ref(true);
const saving = ref(false);
const saved = ref(false);

const currentOutputDir = ref("");

const cfg = reactive<Record<string, any>>({
  language: "zh-CN",
  theme: "light",
  default_task_type: "chat",
  max_tokens: 4096,
  temperature: 0.7,
  port: 8615,
  log_level: "INFO",
  data_dir: "~/.astro-nova",
  knowledge_store: "default",
  notes_dir: "",
});

const defaults = { ...cfg };

function switchLanguage(val: string) {
  locale.value = val;
}

function applyTheme(theme: string) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

onMounted(async () => {
  try {
    const data = await getSettings();
    Object.assign(cfg, data);
  } catch {
    // 使用默认值
  }
  try {
    currentOutputDir.value = await getNovaForgeOutputDir();
  } catch {}
  loading.value = false;
  applyTheme(cfg.theme);
  if (cfg.language === "en") locale.value = "en";
});

async function saveSettings() {
  saving.value = true;
  saved.value = false;
  try {
    applyTheme(cfg.theme);
    const payload: Record<string, any> = {};
    for (const [k, v] of Object.entries(cfg)) {
      if (v !== "" && v !== null && v !== undefined) payload[k] = v;
    }
    await updateSettings(payload);
    saved.value = true;
    ElMessage.success(cfg.language === "en" ? "Settings saved" : "设置已保存");
    setTimeout(() => { saved.value = false; }, 2000);
  } catch {
    ElMessage.error(cfg.language === "en" ? "Save failed" : "保存失败");
  } finally {
    saving.value = false;
  }
}

function resetSettings() {
  Object.assign(cfg, defaults);
  ElMessage.info(cfg.language === "en" ? "Reset to defaults (not saved yet)" : "已重置为默认值（尚未保存）");
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.loading-wrap { display: flex; align-items: center; gap: 8px; color: #909399; font-size: 14px; }
.settings-form { max-width: 700px; }
.sec-card { margin-bottom: 16px; }
.sec-title { font-weight: 600; font-size: 15px; color: #1a1a2e; }
.form-tip { color: #c0c4cc; font-size: 12px; margin: 4px 0 0; }
.form-actions { display: flex; align-items: center; gap: 12px; margin-top: 20px; }
.save-hint { display: flex; align-items: center; gap: 4px; color: #67c23a; font-size: 13px; }
</style>
