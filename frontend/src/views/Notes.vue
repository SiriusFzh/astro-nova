<template>
  <div class="page">
    <div class="page-header">
      <h2>NovaForge 笔记管理</h2>
      <div class="header-actions">
        <!-- 模式选择 -->
        <el-select v-model="selectedMode" style="width:140px" placeholder="模板模式">
          <el-option
            v-for="m in modes" :key="m.id"
            :label="m.name" :value="m.id"
          />
        </el-select>
        <el-input v-model="arxivInput" placeholder="arXiv ID (如 2301.00001)" style="width:200px" clearable />
        <el-button type="primary" @click="generateFromArxiv" :loading="generating">
          生成笔记
        </el-button>
      </div>
    </div>
    <p class="page-desc">
      输入 arXiv ID，AI 将自动下载论文 → 分析内容 → 用 NovaForge 生成笔记
      （LaTeX + Markdown + PDF）。笔记存储在 <code>{{ outputDir }}</code>
    </p>

    <!-- 生成结果预览 -->
    <div v-if="generatedNote" class="note-preview">
      <el-card shadow="never">
        <template #header>
          <div class="preview-header">
            <el-tooltip :content="generatedNote.title" placement="top">
              <span class="preview-title">{{ generatedNote.title?.slice(0, 60) }}</span>
            </el-tooltip>
            <div class="preview-actions">
              <el-tag size="small" effect="plain" type="warning">LaTeX</el-tag>
              <el-tag size="small" effect="plain" type="info" style="margin-left:6px">Markdown</el-tag>
              <el-tag v-if="pdfAvailable" size="small" effect="plain" type="success" style="margin-left:6px">PDF</el-tag>
              <el-button size="small" text @click="copyLatex">复制 LaTeX</el-button>
              <el-button size="small" text @click="copyMD">复制 Markdown</el-button>
              <el-button v-if="pdfAvailable" size="small" @click="openInSystem">系统打开</el-button>
              <el-button v-if="pdfAvailable" type="primary" size="small" @click="exportPdf">下载 PDF</el-button>
            </div>
          </div>
        </template>

        <el-tabs v-model="previewTab" class="preview-tabs">
          <el-tab-pane label="PDF 预览" name="pdf" :disabled="!pdfAvailable">
            <div class="pdf-toolbar">
              <el-button type="primary" size="small" @click="exportPdf" :icon="Download">下载 PDF</el-button>
              <span class="pdf-toolbar-hint">点击下载选择保存位置</span>
            </div>
            <iframe
              v-if="pdfUrl"
              class="pdf-viewer"
              :src="pdfUrl"
              frameborder="0"
            ></iframe>
            <el-empty v-else description="请先编译 PDF" />
          </el-tab-pane>
          <el-tab-pane label="LaTeX 源码" name="latex">
            <div class="code-block">
              <pre><code>{{ generatedNote.latex || '无 LaTeX 内容' }}</code></pre>
              <el-button
                v-if="generatedNote.tex_path"
                size="small"
                class="code-recompile"
                @click="recompileNote"
                :loading="recompiling"
              >重新编译 PDF</el-button>
            </div>
          </el-tab-pane>
          <el-tab-pane label="Markdown" name="md">
            <pre class="code-block"><code>{{ generatedNote.md || '无 Markdown 内容' }}</code></pre>
          </el-tab-pane>
          <el-tab-pane label="文件" name="files">
            <div class="files-list">
              <div v-for="(path, type) in generatedNote.files" :key="type" class="file-item">
                <el-icon :size="16"><Document /></el-icon>
                <span class="file-type">{{ type.toUpperCase() }}</span>
                <span class="file-path">{{ path }}</span>
                <el-button
                  v-if="type === 'pdf'"
                  size="small"
                  text
                  @click="openFile(path)"
                >打开</el-button>
              </div>
              <p class="files-dir">📁 {{ generatedNote.tex_path ? generatedNote.tex_path.substring(0, generatedNote.tex_path.lastIndexOf('\\')) : outputDir }}</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 笔记列表 -->
    <div class="notes-section">
      <div class="notes-section-header">
        <h3>已生成的笔记 ({{ notes.length }})</h3>
        <el-button size="small" text @click="refreshNotes">刷新</el-button>
      </div>

      <el-empty v-if="!loading && notes.length === 0" description="暂无笔记，输入 arXiv ID 生成第一篇" />

      <div v-for="n in notes" :key="n.id" class="note-card" @click="viewNote(n)">
        <div class="note-card-left">
          <el-icon :size="20" color="#1a237e"><Document /></el-icon>
        </div>
        <div class="note-card-body">
          <div class="note-card-title">{{ n.title }}</div>
          <div class="note-card-meta">
            <span>{{ n.id }}</span>
            <span>·</span>
            <span>{{ n.created_at }}</span>
          </div>
        </div>
        <div class="note-card-tags">
          <el-tag v-if="n.has_pdf" size="small" type="success">PDF</el-tag>
          <el-tag v-if="n.has_tex" size="small" type="warning">TeX</el-tag>
          <el-tag v-if="n.has_md" size="small" type="info">MD</el-tag>
        </div>
        <div class="note-card-actions">
          <el-button v-if="n.has_pdf" size="small" text @click.stop="openFile(n.pdf_path)">
            <el-icon><View /></el-icon>
          </el-button>
          <el-button size="small" text @click.stop="confirmDelete(n)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  listNotes, generateNote, readPaper,
  recompileNote as apiRecompile,
  getNovaForgeModes,
} from "@/api/client";
import { ElMessage, ElMessageBox } from "element-plus";
import { Document, View, Delete, Download } from "@element-plus/icons-vue";
import { invoke } from "@tauri-apps/api/core";

const API_BASE = "http://127.0.0.1:8615";

// ── State ──
const notes = ref<any[]>([]);
const loading = ref(false);
const generating = ref(false);
const recompiling = ref(false);
const arxivInput = ref("");
const selectedMode = ref("research-note");
const modes = ref<any[]>([]);
const generatedNote = ref<any>(null);
const previewTab = ref("pdf");
const outputDir = ref("");

// ── Computed ──
const pdfAvailable = computed(() => generatedNote.value?.pdf_available || !!generatedNote.value?.files?.pdf);
const pdfUrl = computed(() => {
  if (generatedNote.value?.arxiv_id) {
    return `${API_BASE}/api/tools/notes/pdf/${generatedNote.value.arxiv_id}`;
  }
  return "";
});

// ── Parse arXiv ID ──
function parseArxivId(input: string): string {
  const s = input.trim();
  const m = s.match(/(\d{4}\.\d{4,5})(v\d+)?/);
  return m ? m[1] : s;
}

// ── Load data ──
onMounted(async () => {
  loading.value = true;
  try {
    const [notesData, modesData] = await Promise.all([
      listNotes(),
      getNovaForgeModes(),
    ]);
    notes.value = notesData || [];
    modes.value = modesData || [];
  } catch (e) {
    console.error("加载失败", e);
    notes.value = [];
    modes.value = [];
    // 获取笔记输出目录
    try {
      outputDir.value = await getNovaForgeOutputDir();
    } catch {
      outputDir.value = "data/notes/";
    }
  } finally {
    loading.value = false;
  }
});

// ── Generate from arXiv ──
async function generateFromArxiv() {
  const id = parseArxivId(arxivInput.value);
  if (!id) {
    ElMessage.warning("请输入有效的 arXiv ID");
    return;
  }

  generating.value = true;
  generatedNote.value = null;
  previewTab.value = "pdf";

  try {
    // Step 1: 读取论文
    ElMessage.info("正在读取论文...");
    const paper = await readPaper(id);
    if (paper.error) {
      ElMessage.error(paper.error);
      return;
    }

    // Step 2: 用 NovaForge 生成笔记
    ElMessage.info("正在生成笔记...");
    const note = await generateNote(
      id,
      paper.title || id,
      paper.note || "",
      selectedMode.value,
      true,  // compile_pdf
    );

    generatedNote.value = {
      ...note,
      title: paper.title || id,
    };

    // Step 3: 刷新列表
    notes.value = await listNotes();
    ElMessage.success("笔记生成成功！");
  } catch (e: any) {
    const detail = e.response?.data?.detail || e.message || String(e);
    ElMessage.error("生成失败: " + detail);
  } finally {
    generating.value = false;
  }
}

// ── Recompile ──
async function recompileNote() {
  const id = generatedNote.value?.arxiv_id;
  if (!id) return;
  recompiling.value = true;
  try {
    const result = await apiRecompile(id);
    ElMessage.success("重新编译成功");
    // Force refresh PDF iframe
    const oldTab = previewTab.value;
    previewTab.value = "latex";
    await new Promise(r => setTimeout(r, 100));
    previewTab.value = oldTab === "pdf" ? "pdf" : "pdf";
  } catch (e: any) {
    ElMessage.error("编译失败: " + (e.message || String(e)));
  } finally {
    recompiling.value = false;
  }
}

// ── View note ──
async function viewNote(n: any) {
  // 加载笔记详情
  generatedNote.value = null;
  previewTab.value = "pdf";
  try {
    const resp = await fetch(`${API_BASE}/api/tools/notes/info/${n.id}`);
    if (resp.ok) {
      const info = await resp.json();
      // 读取 LaTeX 和 MD 内容
      let latex = "", md = "";
      if (info.tex_path) {
        const lr = await fetch(`http://127.0.0.1:8615/api/tools/read-file?path=${encodeURIComponent(info.tex_path)}`);
        if (lr.ok) latex = (await lr.json()).content || "";
      }
      if (info.md_path) {
        const mr = await fetch(`http://127.0.0.1:8615/api/tools/read-file?path=${encodeURIComponent(info.md_path)}`);
        if (mr.ok) md = (mr.ok ? (await mr.json()).content : "") || "";
      }
      generatedNote.value = {
        arxiv_id: n.id,
        title: n.title,
        latex,
        md,
        tex_path: info.tex_path,
        md_path: info.md_path,
        pdf_path: info.pdf_path,
        pdf_available: info.has_pdf,
        files: {
          tex: info.tex_path,
          md: info.md_path,
          pdf: info.pdf_path,
        },
      };
    }
  } catch (e) {
    ElMessage.error("加载笔记失败");
  }
}

// ── Delete ──
function confirmDelete(n: any) {
  ElMessageBox.confirm(
    `确定要删除笔记「${n.title}」吗？\n此操作不可恢复。`,
    "确认删除",
    { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" }
  ).then(async () => {
    try {
      const { deleteNote } = await import("@/api/client");
      await deleteNote(n.id);
      notes.value = notes.value.filter((x: any) => x.id !== n.id);
      if (generatedNote.value?.arxiv_id === n.id) {
        generatedNote.value = null;
      }
      ElMessage.success("已删除");
    } catch (e: any) {
      ElMessage.error("删除失败");
    }
  }).catch(() => {});
}

// ── Refresh ──
async function refreshNotes() {
  try {
    notes.value = await listNotes();
  } catch {
    notes.value = [];
  }
}

// ── Clipboard ──
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

// ── File operations ──
function openInSystem() {
  const path = generatedNote.value?.files?.pdf || generatedNote.value?.pdf_path;
  if (!path) { ElMessage.warning("PDF 不存在"); return; }
  openFile(path);
}

async function openFile(path: string) {
  try {
    await invoke("open_file", { path });
  } catch (e) {
    ElMessage.error("打开失败: " + String(e));
  }
}

async function exportPdf() {
  const path = generatedNote.value?.files?.pdf || generatedNote.value?.pdf_path;
  if (!path) { ElMessage.warning("PDF 不存在"); return; }
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({
      defaultPath: `${generatedNote.value.arxiv_id || "note"}.pdf`,
      filters: [{ name: "PDF", extensions: ["pdf"] }],
    });
    if (dest) {
      await invoke("export_file", { src: path, dest });
      ElMessage.success("导出成功");
    }
  } catch (e) {
    ElMessage.error("导出失败: " + String(e));
  }
}
</script>

<style scoped>
.page { padding: 24px; height: 100%; display: flex; flex-direction: column; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 16px; }
.page-desc code { background: #f0f2f5; padding: 1px 6px; border-radius: 3px; }

/* Preview */
.note-preview { margin-bottom: 20px; }
.preview-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.preview-title { font-weight: 600; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 300px; }
.preview-actions { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.preview-tabs { margin-top: 4px; }
.pdf-viewer { width: 100%; height: 60vh; border: 1px solid #e4e7ed; border-radius: 4px; background: #fff; }
.pdf-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.pdf-toolbar-hint { font-size: 12px; color: #909399; }
.code-block { position: relative; }
.code-block pre { background: #1e1e2e; color: #cdd6f4; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5; max-height: 50vh; overflow-y: auto; white-space: pre-wrap; }
.code-recompile { position: absolute; top: 8px; right: 8px; }
.files-list { padding: 12px; }
.file-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.file-type { font-weight: 600; font-size: 12px; color: #1a237e; min-width: 40px; }
.file-path { flex: 1; font-size: 12px; color: #606266; word-break: break-all; }
.files-dir { margin-top: 12px; font-size: 12px; color: #909399; }

/* Notes list */
.notes-section { flex: 1; overflow-y: auto; }
.notes-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.notes-section-header h3 { margin: 0; font-size: 16px; color: #303133; }
.note-card { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #fff; border: 1px solid #e4e7ed; border-radius: 8px; margin-bottom: 8px; cursor: pointer; transition: all 0.15s; }
.note-card:hover { border-color: #1a237e; box-shadow: 0 2px 8px rgba(26,35,126,0.08); }
.note-card-left { flex-shrink: 0; }
.note-card-body { flex: 1; min-width: 0; }
.note-card-title { font-size: 14px; font-weight: 500; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.note-card-meta { font-size: 12px; color: #909399; display: flex; gap: 6px; }
.note-card-tags { display: flex; gap: 4px; flex-shrink: 0; }
.note-card-actions { display: flex; gap: 4px; flex-shrink: 0; opacity: 0; transition: opacity 0.15s; }
.note-card:hover .note-card-actions { opacity: 1; }

/* Dark theme */
[data-theme="dark"] .page-header h2 { color: #e0e0e0; }
[data-theme="dark"] .pdf-viewer { border-color: #0f3460; }
[data-theme="dark"] .page-desc code { background: #1a2a4a; }
[data-theme="dark"] .note-card { background: #16213e; border-color: #0f3460; }
[data-theme="dark"] .note-card-title { color: #e0e0e0; }
[data-theme="dark"] .notes-section-header h3 { color: #e0e0e0; }
[data-theme="dark"] .file-item { border-bottom-color: #0f3460; }
[data-theme="dark"] .file-path { color: #b0b0c0; }
</style>
