<template>
  <div class="page">
    <div class="page-header"><h2>科研制图</h2></div>
    <p class="page-desc">描述数据并选择图表类型，AI 将生成可运行的出版级 matplotlib 代码（PDF 矢量图）。</p>
    <div class="fig-layout">
      <div class="fig-input">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="6"
          placeholder="描述数据和图表要求，例如: 我有 3C 273 的光谱数据，波长 4000-7000Å，流量 1e-15 量级，标注 Hα、Hβ、[OIII] 发射线"
        />
        <div class="fig-opts-row">
          <el-select v-model="plotType" style="width:160px">
            <el-option label="光谱图" value="spectrum" />
            <el-option label="光变曲线" value="lightcurve" />
            <el-option label="SED 能谱分布" value="sed" />
            <el-option label="等高线图" value="contour" />
            <el-option label="直方图" value="histogram" />
            <el-option label="散点图" value="scatter" />
            <el-option label="多面板组合图" value="multi_panel" />
          </el-select>
          <el-select v-model="style" style="width:160px">
            <el-option label="ApJ 风格" value="apj" />
            <el-option label="MNRAS 风格" value="mnras" />
            <el-option label="A&A 风格" value="aa" />
          </el-select>
          <el-input v-model="extraReq" placeholder="额外要求（色板、标注等）" clearable style="flex:1" />
          <el-button type="primary" @click="generateCode" :loading="loading">生成代码</el-button>
        </div>
      </div>
      <div class="fig-output" v-if="code || error">
        <div class="output-header">
          <span>生成的 Python 代码</span>
          <span class="output-info">
            <el-tag v-if="filePath" size="small" type="success">{{ filePath }}</el-tag>
          </span>
          <el-button size="small" @click="copyCode" :disabled="!code">复制</el-button>
        </div>
        <pre class="code-block"><code>{{ code || error }}</code></pre>
      </div>
    </div>
    <el-empty v-if="!loading && !code && !error" description="输入数据描述并点击生成" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { generateFigureCode } from "@/api/client";
import { ElMessage } from "element-plus";

const prompt = ref("");
const plotType = ref("spectrum");
const style = ref("apj");
const extraReq = ref("");
const loading = ref(false);
const code = ref("");
const error = ref("");
const filePath = ref("");

async function generateCode() {
  if (!prompt.value.trim()) { ElMessage.warning("请输入数据描述"); return; }
  loading.value = true;
  code.value = "";
  error.value = "";
  filePath.value = "";
  try {
    const data = await generateFigureCode(prompt.value, plotType.value, style.value);
    if (data.error) {
      error.value = data.error;
    } else {
      code.value = data.code || data.slides || "无返回";
      filePath.value = data.file_path || "";
      ElMessage.success("代码已生成");
    }
  } catch (e: any) {
    error.value = "请求失败: " + (e?.message || String(e));
    ElMessage.error("生成失败");
  } finally {
    loading.value = false;
  }
}

function copyCode() {
  navigator.clipboard.writeText(code.value);
  ElMessage.success("已复制到剪贴板");
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
