<template>
  <div class="page">
    <div class="page-header"><h2>通用设置</h2></div>
    <p class="page-desc">配置 AstroNova 运行参数、界面偏好和默认行为。</p>

    <div v-if="loading" class="loading-wrap"><el-icon class="is-loading" :size="24"><Loading /></el-icon> 加载中...</div>

    <el-form v-else label-position="top" class="settings-form">
      <!-- 界面 -->
      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">界面</span></template>
        <el-form-item label="界面语言">
          <el-radio-group v-model="cfg.language">
            <el-radio value="zh-CN">简体中文</el-radio>
            <el-radio value="en">English</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="主题">
          <el-radio-group v-model="cfg.theme">
            <el-radio value="light">浅色</el-radio>
            <el-radio value="dark">深色</el-radio>
            <el-radio value="auto">跟随系统</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-card>

      <!-- LLM 默认参数 -->
      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">LLM 默认参数</span></template>
        <el-form-item label="默认任务类型">
          <el-select v-model="cfg.default_task_type" style="width:240px">
            <el-option label="通用对话 (chat)" value="chat" />
            <el-option label="文献搜索与精读 (search/read)" value="search" />
            <el-option label="笔记生成 (write)" value="write" />
            <el-option label="制图代码 (code)" value="code" />
          </el-select>
          <p class="form-tip">选择 Provider 时若 task_route 匹配此值则优先使用</p>
        </el-form-item>
        <el-form-item label="最大输出 Token">
          <el-input-number v-model="cfg.max_tokens" :min="512" :max="32768" :step="512" />
          <p class="form-tip">限制 LLM 单次回复的最大 token 数</p>
        </el-form-item>
        <el-form-item label="Temperature">
          <el-slider v-model="cfg.temperature" :min="0" :max="2" :step="0.1" style="width:300px" />
          <p class="form-tip">较低值使输出更确定，较高值更有创造力（默认 0.7）</p>
        </el-form-item>
      </el-card>

      <!-- 服务 -->
      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">服务</span></template>
        <el-form-item label="后端端口">
          <el-input-number v-model="cfg.port" :min="1024" :max="65535" />
          <p class="form-tip">重启后生效，默认 8615</p>
        </el-form-item>
        <el-form-item label="日志等级">
          <el-select v-model="cfg.log_level" style="width:180px">
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
        </el-form-item>
      </el-card>

      <!-- 存储 -->
      <el-card shadow="never" class="sec-card">
        <template #header><span class="sec-title">存储与路径</span></template>
        <el-form-item label="数据目录">
          <el-input v-model="cfg.data_dir" placeholder="~/.astro-nova" />
          <p class="form-tip">论文、笔记、知识库存储位置</p>
        </el-form-item>
        <el-form-item label="知识库默认存储">
          <el-input v-model="cfg.knowledge_store" placeholder="default" />
        </el-form-item>
      </el-card>

      <!-- 保存 -->
      <div class="form-actions">
        <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        <el-button @click="resetSettings">重置为默认</el-button>
        <span v-if="saved" class="save-hint"><el-icon color="#67c23a"><SuccessFilled /></el-icon> 已保存</span>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { getSettings, updateSettings } from "@/api/client";
import { ElMessage } from "element-plus";
import { Loading, SuccessFilled } from "@element-plus/icons-vue";

const loading = ref(true);
const saving = ref(false);
const saved = ref(false);

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
});

const defaults = { ...cfg };

onMounted(async () => {
  try {
    const data = await getSettings();
    Object.assign(cfg, data);
  } catch {
    // 使用默认值
  } finally {
    loading.value = false;
  }
});

async function saveSettings() {
  saving.value = true;
  saved.value = false;
  try {
    // 只保存非空字段
    const payload: Record<string, any> = {};
    for (const [k, v] of Object.entries(cfg)) {
      if (v !== "" && v !== null && v !== undefined) payload[k] = v;
    }
    await updateSettings(payload);
    saved.value = true;
    ElMessage.success("设置已保存");
    setTimeout(() => { saved.value = false; }, 2000);
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

function resetSettings() {
  Object.assign(cfg, defaults);
  ElMessage.info("已重置为默认值（尚未保存）");
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
