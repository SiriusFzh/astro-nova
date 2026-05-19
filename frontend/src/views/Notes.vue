<template>
  <div class="page">
    <div class="page-header">
      <h2>笔记</h2>
      <div class="header-actions">
        <el-input v-model="arxivId" placeholder="arXiv ID，如 2301.00001" style="width:200px" clearable />
        <el-button type="primary" @click="generateFromArxiv" :loading="generating">从 arXiv 生成笔记</el-button>
      </div>
    </div>
    <p class="page-desc">科研笔记管理 — 从 arXiv 论文生成 NovaForge 格式笔记（LaTeX + Markdown）。</p>

    <el-empty v-if="!loading && notes.length === 0" description="还没有笔记" />

    <div v-if="generatedNote" class="note-preview">
      <el-card shadow="never">
        <template #header>
          <div class="preview-header">
            <span>{{ generatedNote.title }}</span>
            <div>
              <el-tag size="small" type="warning">LaTeX</el-tag>
              <el-tag size="small" type="info" style="margin-left:6px">Markdown</el-tag>
              <el-button size="small" style="margin-left:12px" @click="copyLatex">复制 LaTeX</el-button>
              <el-button size="small" @click="copyMD">复制 Markdown</el-button>
            </div>
          </div>
        </template>
        <pre class="note-code"><code>{{ generatedNote.latex?.slice(0, 2000) || generatedNote.md?.slice(0, 2000) || "（无内容）" }}</code></pre>
        <div v-if="generatedNote.file_paths" class="preview-files">
          <el-tag v-if="generatedNote.file_paths.tex" size="small" type="success">{{ generatedNote.file_paths.tex }}</el-tag>
          <el-tag v-if="generatedNote.file_paths.md" size="small" type="success" style="margin-left:6px">{{ generatedNote.file_paths.md }}</el-tag>
        </div>
      </el-card>
    </div>

    <el-card v-for="n in notes" :key="n.id" class="note-card" shadow="hover">
      <div class="note-header">
        <span class="note-title">{{ n.title }}</span>
        <el-tag size="small" :type="n.format === 'latex' ? 'warning' : 'info'">{{ n.format }}</el-tag>
        <span class="note-date">{{ n.created_at }}</span>
      </div>
      <div class="note-tags" v-if="n.tags">
        <el-tag size="small" v-for="t in n.tags.split(',')" :key="t" type="info" effect="plain">{{ t }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { listNotes, generateNote, readPaper } from "@/api/client";
import { ElMessage } from "element-plus";

const notes = ref<any[]>([]);
const loading = ref(false);
const arxivId = ref("");
const generating = ref(false);
const generatedNote = ref<any>(null);

onMounted(async () => {
  loading.value = true;
  try { notes.value = await listNotes(); } catch {} finally { loading.value = false; }
});

async function generateFromArxiv() {
  const id = arxivId.value.trim();
  if (!id) { ElMessage.warning("请输入 arXiv ID"); return; }

  generating.value = true;
  generatedNote.value = null;
  try {
    // 先精读
    const paper = await readPaper(id);
    if (paper.error) { ElMessage.error(paper.error); return; }

    // 再生成笔记
    const note = await generateNote(id, paper.title || id, paper.note || "");
    if (note.error) { ElMessage.error(note.error); return; }

    generatedNote.value = { ...note, title: paper.title || id };
    ElMessage.success("笔记生成完成");
  } catch (e: any) {
    ElMessage.error("生成失败: " + (e?.message || String(e)));
  } finally {
    generating.value = false;
  }
}

function copyLatex() {
  if (generatedNote.value?.latex) {
    navigator.clipboard.writeText(generatedNote.value.latex);
    ElMessage.success("LaTeX 已复制");
  }
}

function copyMD() {
  if (generatedNote.value?.md) {
    navigator.clipboard.writeText(generatedNote.value.md);
    ElMessage.success("Markdown 已复制");
  }
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.note-card { margin-bottom: 12px; }
.note-header { display: flex; align-items: center; gap: 12px; }
.note-title { font-weight: 600; font-size: 15px; color: #303133; }
.note-date { font-size: 12px; color: #909399; margin-left: auto; }
.note-tags { margin-top: 8px; display: flex; gap: 6px; }
.note-preview { margin-bottom: 20px; }
.preview-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.note-code { background: #1e1e2e; color: #cdd6f4; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5; max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
.preview-files { margin-top: 8px; }
</style>
