<template>
  <div class="page">
    <div class="page-header"><h2>PPT 生成</h2></div>
    <p class="page-desc">从论文或笔记一键生成学术汇报幻灯片（支持 Marp/Pandoc/Reveal.js）。</p>
    <div class="ppt-form">
      <el-card shadow="never" class="ppt-card">
        <template #header>输入来源</template>
        <el-radio-group v-model="sourceType" style="margin-bottom:12px">
          <el-radio value="arxiv">arXiv ID</el-radio>
          <el-radio value="manual">手动输入</el-radio>
        </el-radio-group>
        <div v-if="sourceType === 'arxiv'">
          <el-input v-model="arxivId" placeholder="输入 arXiv ID，如 2301.00001" clearable style="margin-bottom:8px" />
          <el-button size="small" @click="fetchAndFill" :loading="fetching">获取论文信息</el-button>
          <el-input v-if="fetchedTitle" v-model="slideTitle" placeholder="标题" style="margin-top:8px" />
        </div>
        <el-input
          v-else
          v-model="manualInput"
          type="textarea"
          :rows="8"
          placeholder="输入论文精读笔记或论文内容（标题、作者、摘要、核心结果等）"
        />
      </el-card>
      <el-card shadow="never" class="ppt-card">
        <template #header>幻灯片设置</template>
        <div class="ppt-opts">
          <el-select v-model="slideStyle" style="width:160px">
            <el-option label="课题汇报（中文详细，10-15页）" value="journal_club" />
            <el-option label="国际会议（English，8-10页）" value="conference" />
            <el-option label="答辩/开题（中英混合，15-20页）" value="defense" />
          </el-select>
          <el-select v-model="outputFormat" style="width:140px">
            <el-option label="Marp" value="marp" />
            <el-option label="Pandoc" value="pandoc" />
            <el-option label="Reveal.js" value="revealjs" />
          </el-select>
          <el-button type="primary" @click="generatePPT" :loading="generating">生成 PPT</el-button>
        </div>
      </el-card>
    </div>

    <el-empty v-if="!generating && !slideContent" description="选择来源并生成幻灯片" />

    <div v-if="slideContent" class="ppt-result">
      <el-card shadow="never">
        <template #header>
          <div class="ppt-result-header">
            <span>幻灯片预览 ({{ styleName }})</span>
            <div class="ppt-result-actions">
              <el-tag v-if="filePath" size="small" type="success">{{ filePath }}</el-tag>
              <el-button size="small" @click="copyContent">复制</el-button>
              <el-button v-if="convertCmd" size="small" type="primary" @click="copyCmd">复制转换命令</el-button>
            </div>
          </div>
        </template>
        <pre class="slide-preview"><code>{{ slideContent }}</code></pre>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { generatePPT as apiGeneratePPT, fetchPaper } from "@/api/client";
import { ElMessage } from "element-plus";

const sourceType = ref("arxiv");
const arxivId = ref("");
const slideTitle = ref("");
const manualInput = ref("");
const slideStyle = ref("journal_club");
const outputFormat = ref("marp");
const generating = ref(false);
const fetching = ref(false);
const fetchedTitle = ref("");
const slideContent = ref("");
const filePath = ref("");
const convertCmd = ref("");
const styleName = ref("");

async function fetchAndFill() {
  if (!arxivId.value.trim()) return;
  fetching.value = true;
  try {
    const data = await fetchPaper(arxivId.value.trim());
    if (data.paper) {
      fetchedTitle.value = data.paper.title || "";
      slideTitle.value = fetchedTitle.value;
      if (!manualInput.value) {
        manualInput.value = `标题: ${data.paper.title}\n作者: ${(data.paper.authors || []).join(", ")}\n摘要: ${data.paper.summary || ""}`;
      }
      ElMessage.success("已获取论文信息");
    }
  } catch {
    ElMessage.error("获取论文信息失败");
  } finally {
    fetching.value = false;
  }
}

const styleLabels: Record<string, string> = {
  journal_club: "课题汇报",
  conference: "国际会议",
  defense: "答辩/开题",
};

async function generatePPT() {
  let content = manualInput.value;
  let title = slideTitle.value;
  let aid = "";

  if (sourceType.value === "arxiv") {
    aid = arxivId.value.trim();
    if (!content && !aid) { ElMessage.warning("请输入 arXiv ID 或内容"); return; }
  } else {
    if (!content.trim()) { ElMessage.warning("请输入论文内容"); return; }
  }

  generating.value = true;
  slideContent.value = "";
  filePath.value = "";
  convertCmd.value = "";
  styleName.value = styleLabels[slideStyle.value] || slideStyle.value;

  try {
    const data = await apiGeneratePPT(aid, title, content, slideStyle.value, outputFormat.value);
    if (data.error) {
      ElMessage.error(data.error);
    } else {
      slideContent.value = data.slides || "（无返回）";
      filePath.value = data.file_path || "";
      convertCmd.value = data.convert_command || "";
      ElMessage.success("PPT 生成完成");
    }
  } catch (e: any) {
    ElMessage.error("生成失败: " + (e?.message || String(e)));
  } finally {
    generating.value = false;
  }
}

function copyContent() {
  navigator.clipboard.writeText(slideContent.value);
  ElMessage.success("已复制到剪贴板");
}

function copyCmd() {
  navigator.clipboard.writeText(convertCmd.value);
  ElMessage.success("转换命令已复制");
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.ppt-form { display: flex; gap: 20px; margin-bottom: 20px; }
.ppt-card { flex: 1; min-width: 300px; }
.ppt-opts { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.ppt-result { margin-top: 16px; }
.ppt-result-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.ppt-result-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.slide-preview { background: #1e1e2e; color: #cdd6f4; padding: 20px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.7; max-height: 600px; overflow-y: auto; white-space: pre-wrap; }
</style>
