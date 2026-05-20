<template>
  <div class="page">
    <div class="page-header"><h2>{{ $t('ppt.title') }}</h2></div>
    <p class="page-desc">{{ $t('ppt.desc') }}</p>
    <div class="ppt-form">
      <el-card shadow="never" class="ppt-card">
        <template #header>{{ $t('ppt.sourceType') }}</template>
        <el-radio-group v-model="sourceType" style="margin-bottom:12px">
          <el-radio value="arxiv">{{ $t('ppt.arxiv') }}</el-radio>
          <el-radio value="manual">{{ $t('ppt.manual') }}</el-radio>
        </el-radio-group>
        <div v-if="sourceType === 'arxiv'">
          <el-input v-model="arxivId" :placeholder="$t('ppt.arxivPlaceholder')" clearable style="margin-bottom:8px" />
          <el-button size="small" @click="fetchAndFill" :loading="fetching">{{ $t('ppt.fetchTitle') }}</el-button>
          <el-input v-if="fetchedTitle" v-model="slideTitle" :placeholder="$t('ppt.arxiv')" style="margin-top:8px" />
        </div>
        <el-input
          v-else
          v-model="manualInput"
          type="textarea"
          :rows="8"
          :placeholder="$t('ppt.manualPlaceholder')"
        />
      </el-card>
      <el-card shadow="never" class="ppt-card">
        <template #header>{{ $t('ppt.slideSettings') }}</template>
        <div class="ppt-opts">
          <el-select v-model="slideStyle" style="width:160px">
            <el-option :label="$t('ppt.styles.journal_club')" value="journal_club" />
            <el-option :label="$t('ppt.styles.conference')" value="conference" />
            <el-option :label="$t('ppt.styles.defense')" value="defense" />
          </el-select>
          <el-select v-model="outputFormat" style="width:140px">
            <el-option :label="$t('ppt.formats.marp')" value="marp" />
            <el-option :label="$t('ppt.formats.pandoc')" value="pandoc" />
            <el-option :label="$t('ppt.formats.revealjs')" value="revealjs" />
          </el-select>
          <el-button type="primary" @click="generatePPT" :loading="generating">{{ $t('ppt.generate') }}</el-button>
        </div>
      </el-card>
    </div>

    <el-empty v-if="!generating && !slideContent" :description="$t('ppt.emptyHint')" />

    <div v-if="slideContent" class="ppt-result">
      <el-card shadow="never">
        <template #header>
          <div class="ppt-result-header">
            <span>{{ $t('ppt.preview') }} ({{ styleName }})</span>
            <div class="ppt-result-actions">
              <el-tag v-if="filePath" size="small" type="success">{{ filePath }}</el-tag>
              <el-button size="small" @click="copyContent">{{ $t('ppt.copyContent') }}</el-button>
              <el-button v-if="convertCmd" size="small" type="primary" @click="copyCmd">{{ $t('ppt.copyCmd') }}</el-button>
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
import { useI18n } from "vue-i18n";
import { generatePPT as apiGeneratePPT, fetchPaper } from "@/api/client";
import { ElMessage } from "element-plus";

const { t } = useI18n();

const styleLabels: Record<string, string> = {
  journal_club: t('ppt.styles.journal_club'),
  conference: t('ppt.styles.conference'),
  defense: t('ppt.styles.defense'),
};

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
        manualInput.value = `${t('writing.title')}: ${data.paper.title}\nAuthors: ${(data.paper.authors || []).join(", ")}\nAbstract: ${data.paper.summary || ""}`;
      }
      ElMessage.success(t('ppt.fetchSuccess'));
    }
  } catch {
    ElMessage.error(t('ppt.fetchFailed'));
  } finally {
    fetching.value = false;
  }
}

async function generatePPT() {
  let content = manualInput.value;
  let title = slideTitle.value;
  let aid = "";

  if (sourceType.value === "arxiv") {
    aid = arxivId.value.trim();
    if (!content && !aid) { ElMessage.warning(t('ppt.warningInputArxiv')); return; }
  } else {
    if (!content.trim()) { ElMessage.warning(t('ppt.warningInputContent')); return; }
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
      slideContent.value = data.slides || t('ppt.noReturn');
      filePath.value = data.file_path || "";
      convertCmd.value = data.convert_command || "";
      ElMessage.success(t('ppt.generateSuccess'));
    }
  } catch (e: any) {
    ElMessage.error(t('ppt.generateFailed') + ": " + (e?.message || String(e)));
  } finally {
    generating.value = false;
  }
}

function copyContent() {
  navigator.clipboard.writeText(slideContent.value);
  ElMessage.success(t('ppt.copied'));
}

function copyCmd() {
  navigator.clipboard.writeText(convertCmd.value);
  ElMessage.success(t('ppt.cmdCopied'));
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
