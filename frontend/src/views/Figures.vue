<template>
  <div class="page">
    <div class="page-header"><h2>{{ $t('figures.title') }}</h2></div>
    <p class="page-desc">{{ $t('figures.desc') }}</p>
    <div class="fig-layout">
      <div class="fig-input">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="6"
          :placeholder="$t('figures.promptPlaceholder')"
        />
        <div class="fig-opts-row">
          <el-select v-model="plotType" style="width:160px">
            <el-option :label="$t('figures.plotTypes.spectrum')" value="spectrum" />
            <el-option :label="$t('figures.plotTypes.lightcurve')" value="lightcurve" />
            <el-option :label="$t('figures.plotTypes.sed')" value="sed" />
            <el-option :label="$t('figures.plotTypes.contour')" value="contour" />
            <el-option :label="$t('figures.plotTypes.histogram')" value="histogram" />
            <el-option :label="$t('figures.plotTypes.scatter')" value="scatter" />
            <el-option :label="$t('figures.plotTypes.multi_panel')" value="multi_panel" />
          </el-select>
          <el-select v-model="style" style="width:160px">
            <el-option :label="$t('figures.styles.apj')" value="apj" />
            <el-option :label="$t('figures.styles.mnras')" value="mnras" />
            <el-option :label="$t('figures.styles.aa')" value="aa" />
          </el-select>
          <el-input v-model="extraReq" :placeholder="$t('figures.extraReqPlaceholder')" clearable style="flex:1" />
          <el-button type="primary" @click="generateCode" :loading="loading">{{ $t('figures.generate') }}</el-button>
        </div>
      </div>
      <div class="fig-output" v-if="code || error">
        <div class="output-header">
          <span>{{ $t('figures.generatedCode') }}</span>
          <span class="output-info">
            <el-tag v-if="filePath" size="small" type="success">{{ filePath }}</el-tag>
          </span>
          <el-button size="small" @click="copyCode" :disabled="!code">{{ $t('figures.copy') }}</el-button>
        </div>
        <pre class="code-block"><code>{{ code || error }}</code></pre>
      </div>
    </div>
    <el-empty v-if="!loading && !code && !error" :description="$t('figures.emptyHint')" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { generateFigureCode } from "@/api/client";
import { ElMessage } from "element-plus";

const { t } = useI18n();
const prompt = ref("");
const plotType = ref("spectrum");
const style = ref("apj");
const extraReq = ref("");
const loading = ref(false);
const code = ref("");
const error = ref("");
const filePath = ref("");

async function generateCode() {
  if (!prompt.value.trim()) { ElMessage.warning(t('figures.warningInput')); return; }
  loading.value = true;
  code.value = "";
  error.value = "";
  filePath.value = "";
  try {
    const data = await generateFigureCode(prompt.value, plotType.value, style.value);
    if (data.error) {
      error.value = data.error;
    } else {
      code.value = data.code || data.slides || t('figures.noReturn');
      filePath.value = data.file_path || "";
      ElMessage.success(t('figures.generateSuccess'));
    }
  } catch (e: any) {
    error.value = t('figures.requestFailed') + ": " + (e?.message || String(e));
    ElMessage.error(t('figures.generateFailed'));
  } finally {
    loading.value = false;
  }
}

function copyCode() {
  navigator.clipboard.writeText(code.value);
  ElMessage.success(t('figures.copied'));
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.fig-layout { display: flex; gap: 20px; flex-wrap: wrap; }
.fig-input { flex: 1; min-width: 400px; }
.fig-opts-row { display: flex; gap: 10px; margin-top: 12px; align-items: center; flex-wrap: wrap; }
.fig-output { flex: 1; min-width: 400px; }
.output-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-weight: 600; color: #303133; gap: 8px; flex-wrap: wrap; }
.output-info { flex: 1; font-size: 12px; }
.code-block { background: #1e1e2e; color: #cdd6f4; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5; max-height: 600px; overflow-y: auto; white-space: pre-wrap; }
</style>
