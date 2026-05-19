<template>
  <div class="page">
    <div class="page-header"><h2>论文写作</h2></div>
    <p class="page-desc">选择目标期刊，AI 辅助按标准格式撰写论文各章节，输出 LaTeX。</p>
    <div class="writing-layout">
      <div class="writing-sidebar">
        <el-card shadow="never">
          <template #header>目标期刊</template>
          <el-radio-group v-model="journal" class="journal-list">
            <el-radio value="apj" class="journal-item">ApJ / AJ / ApJL</el-radio>
            <el-radio value="mnras" class="journal-item">MNRAS</el-radio>
            <el-radio value="aa" class="journal-item">A&A</el-radio>
          </el-radio-group>
        </el-card>
        <el-card shadow="never" style="margin-top:12px">
          <template #header>论文章节</template>
          <div
            v-for="sec in sections"
            :key="sec.key"
            class="section-item"
            :class="{ active: activeSection === sec.key, done: sec.done }"
            @click="activeSection = sec.key"
          >
            <el-icon v-if="sec.done" color="#67c23a"><Check /></el-icon>
            <el-icon v-else><Document /></el-icon>
            <span>{{ sec.label }}</span>
            <span v-if="sec.wordCount" class="word-count">{{ sec.wordCount }} 词</span>
          </div>
        </el-card>
        <el-button style="width:100%;margin-top:12px" @click="exportAll">导出全部 LaTeX</el-button>
      </div>
      <div class="writing-main">
        <div class="writing-toolbar">
          <el-input v-model="paperTitle" placeholder="论文标题（可选）" clearable style="flex:1" />
          <el-button :icon="ChatDotSquare" type="primary" @click="writeWithAI" :loading="writing">
            {{ writingSection ? `正在撰写 ${writingSection}...` : 'AI 撰写本段' }}
          </el-button>
        </div>
        <el-input
          v-model="sectionContent"
          type="textarea"
          :rows="16"
          placeholder="在此输入上下文信息（已有结果、数据描述、关键数值、相关文献等），然后点击「AI 撰写本段」生成内容..."
        />
        <div v-if="currentWordCount > 0" class="writing-footer">
          <span>本段约 {{ currentWordCount }} 词 | 期刊字数限制: {{ journalLimit }}</span>
          <el-button size="small" @click="saveSection">保存本段</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { writeSection } from "@/api/client";
import { Check, Document, ChatDotSquare } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const journal = ref("apj");
const paperTitle = ref("");
const activeSection = ref("abstract");
const sectionContent = ref("");
const writing = ref(false);
const writingSection = ref("");

const sections = ref([
  { key: "abstract", label: "Abstract (摘要)", done: false, wordCount: 0 },
  { key: "introduction", label: "Introduction (引言)", done: false, wordCount: 0 },
  { key: "methods", label: "Methods (方法)", done: false, wordCount: 0 },
  { key: "results", label: "Results (结果)", done: false, wordCount: 0 },
  { key: "discussion", label: "Discussion (讨论)", done: false, wordCount: 0 },
  { key: "conclusion", label: "Conclusion (结论)", done: false, wordCount: 0 },
]);

const journalLimit = computed(() => ({
  apj: "摘要 ≤250 词",
  mnras: "摘要 ≤300 词",
  aa: "摘要 ≤300 词",
}[journal.value] || ""));

const currentWordCount = computed(() => {
  const text = sectionContent.value;
  return text ? text.split(/\s+/).filter(Boolean).length : 0;
});

// 切换章节时保存当前内容
const sectionContents = ref<Record<string, string>>({});

function saveSection() {
  sectionContents.value[activeSection.value] = sectionContent.value;
  const sec = sections.value.find(s => s.key === activeSection.value);
  if (sec && sectionContent.value.trim()) {
    sec.done = true;
    sec.wordCount = currentWordCount.value;
  }
}

async function writeWithAI() {
  saveSection();
  const context = sectionContent.value.trim();
  if (!context) {
    ElMessage.warning("请在编辑区输入上下文信息（结果、数据、要求等）");
    return;
  }

  writing.value = true;
  writingSection.value = sections.value.find(s => s.key === activeSection.value)?.label || activeSection.value;

  try {
    const data = await writeSection(
      activeSection.value,
      journal.value,
      paperTitle.value,
      context,
    );
    if (data.error) {
      ElMessage.error(data.error);
    } else {
      sectionContent.value = data.section || "（无返回内容）";
      const sec = sections.value.find(s => s.key === activeSection.value);
      if (sec) {
        sec.done = true;
        sec.wordCount = data.word_count || 0;
        sectionContents.value[activeSection.value] = sectionContent.value;
      }
      ElMessage.success(`${sec?.label || activeSection.value} 撰写完成`);
    }
  } catch (e: any) {
    ElMessage.error("写作失败: " + (e?.message || String(e)));
  } finally {
    writing.value = false;
    writingSection.value = "";
  }
}

function exportAll() {
  saveSection();
  const parts: string[] = [];
  for (const sec of sections.value) {
    const content = sectionContents.value[sec.key];
    if (content && content.trim()) {
      const clean = content.trim().startsWith("\\") ? content : content;
      parts.push(`% === ${sec.label} ===\n${clean}\n`);
    }
  }
  if (parts.length === 0) {
    ElMessage.warning("还没有写好的章节");
    return;
  }
  const full = `% ${paperTitle.value || "Untitled"}\n% Journal: ${journal.value}\n\\documentclass{${journal.value === 'apj' ? 'aastex701' : journal.value === 'mnras' ? 'mnras' : 'aa'}}\n\\begin{document}\n\n${parts.join('\n')}\n\\end{document}\n`;
  const blob = new Blob([full], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `paper_${journal.value}.tex`;
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success("已导出 .tex 文件");
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.writing-layout { display: flex; gap: 20px; }
.writing-sidebar { width: 220px; flex-shrink: 0; }
.journal-list { display: flex; flex-direction: column; gap: 8px; }
.journal-item { margin: 0; }
.section-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; cursor: pointer; border-radius: 6px; font-size: 13px; color: #606266; }
.section-item:hover { background: #f0f2f5; }
.section-item.active { background: #ecf5ff; color: #409eff; }
.section-item.done { color: #67c23a; }
.word-count { margin-left: auto; font-size: 11px; color: #c0c4cc; }
.writing-main { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.writing-toolbar { display: flex; gap: 12px; align-items: center; }
.writing-footer { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #909399; }
</style>
