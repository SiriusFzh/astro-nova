import axios from "axios";

// Tauri v2 生产环境 protocol 为 "https:"，无法用 "/api" 代理到后端
// 无论开发/生产都直连 Python 后端
const API_BASE = "http://127.0.0.1:8615/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,  // 5 分钟（digest 爬 arXiv 需要较长时间）
});

// ── Conversations ──
export async function listConversations() {
  const resp = await api.get("/conversations");
  return resp.data;
}

export async function createConversation(title = "新对话") {
  const resp = await api.post("/conversations", { title });
  return resp.data;
}

export async function getConversation(id: number) {
  const resp = await api.get(`/conversations/${id}`);
  return resp.data;
}

export async function updateConversation(id: number, data: { title?: string; messages?: any[] }) {
  const resp = await api.put(`/conversations/${id}`, data);
  return resp.data;
}

export async function deleteConversation(id: number) {
  const resp = await api.delete(`/conversations/${id}`);
  return resp.data;
}

export async function editMessage(convId: number, msgIdx: number, content: string) {
  const resp = await api.patch(`/conversations/${convId}/messages/${msgIdx}`, { index: msgIdx, content });
  return resp.data;
}

export async function deleteMessage(convId: number, msgIdx: number) {
  const resp = await api.delete(`/conversations/${convId}/messages/${msgIdx}`);
  return resp.data;
}

// ── Chat ──
export async function chat(messages: any[], taskType = "chat") {
  const resp = await api.post("/chat", { messages, task_type: taskType });
  return resp.data;
}

// ── Providers ──
export async function getProviders() {
  const resp = await api.get("/providers");
  return resp.data;
}

export async function createProvider(cfg: any) {
  const resp = await api.post("/providers", cfg);
  return resp.data;
}

export async function deleteProvider(id: number) {
  const resp = await api.delete(`/providers/${id}`);
  return resp.data;
}

// ── Papers ──
export async function searchPapers(query: string, maxResults = 10, categories = ["astro-ph"]) {
  const resp = await api.post("/tools/arxiv/search", { query, max_results: maxResults, categories });
  return resp.data;
}

export async function fetchPaper(arxivId: string) {
  const resp = await api.post("/tools/arxiv/fetch", { arxiv_id: arxivId });
  return resp.data;
}

export async function listPapers() {
  const resp = await api.get("/papers");
  return resp.data;
}

export async function deletePaper(arxivId: string) {
  const resp = await api.delete(`/papers/${arxivId}`);
  return resp.data;
}

// ── Paper Reader ──
export async function readPaper(arxivId: string, language = "中文") {
  const resp = await api.post("/tools/read", { arxiv_id: arxivId, language });
  return resp.data;
}

// ── Notes (NovaForge) ──
export async function listNotes() {
  const resp = await api.get("/tools/notes/list");
  return resp.data.notes || [];
}

export async function deleteNote(arxivId: string) {
  const resp = await api.delete(`/tools/notes/${arxivId}`);
  return resp.data;
}

export async function getNoteInfo(arxivId: string) {
  const resp = await api.get(`/tools/notes/info/${arxivId}`);
  return resp.data;
}

export async function generateNote(arxivId: string, title: string, content = "", mode = "research-note", compilePdf = true) {
  const resp = await api.post("/tools/note", {
    arxiv_id: arxivId,
    title,
    content,
    mode,
    compile_pdf: compilePdf,
  });
  return resp.data;
}

export async function recompileNote(arxivId: string) {
  const resp = await api.post(`/tools/notes/recompile/${arxivId}`);
  return resp.data;
}

export async function getNovaForgeModes() {
  const resp = await api.get("/tools/novaforge/modes");
  return resp.data.modes || [];
}

export async function getNovaForgeOutputDir() {
  const resp = await api.get("/tools/novaforge/output-dir");
  return resp.data.path || "";
}

// ── Figure Code Generator ──
export async function generateFigureCode(dataDescription: string, plotType = "spectrum", style = "apj") {
  const resp = await api.post("/tools/figure", {
    data_description: dataDescription,
    plot_type: plotType,
    style,
  });
  return resp.data;
}

// ── Writing Assistant ──
export async function writeSection(sectionType: string, journal = "apj", title = "", context = "") {
  const resp = await api.post("/tools/write", {
    section_type: sectionType,
    journal,
    title,
    context,
  });
  return resp.data;
}

// ── PPT Generator ──
export async function generatePPT(arxivId = "", title = "", content = "", style = "journal_club", outputFormat = "marp") {
  const resp = await api.post("/tools/ppt", {
    arxiv_id: arxivId,
    title,
    content,
    style,
    output_format: outputFormat,
  });
  return resp.data;
}

// ── Knowledge Base ──
export async function knowledgeSearch(query: string, store = "default", topK = 10) {
  const resp = await api.post("/knowledge/search", { query, store, top_k: topK });
  return resp.data;
}

export async function getKnowledgeInfo(store = "default") {
  const resp = await api.get(`/knowledge/stores/${store}`);
  return resp.data;
}

// ── Skills ──
export async function getSkills() {
  const resp = await api.get("/skills");
  return resp.data;
}

export async function toggleSkill(name: string, active: boolean) {
  const resp = await api.post(`/skills/${name}/${active ? "activate" : "deactivate"}`);
  return resp.data;
}

// ── Plugins ──
export async function getPlugins() {
  const resp = await api.get("/plugins");
  return resp.data;
}

export async function loadPlugin(name: string) {
  const resp = await api.post(`/plugins/${name}/load`);
  return resp.data;
}

export async function unloadPlugin(name: string) {
  const resp = await api.post(`/plugins/${name}/unload`);
  return resp.data;
}

export async function reloadPlugin(name: string) {
  const resp = await api.post(`/plugins/${name}/reload`);
  return resp.data;
}

export async function scanPlugins() {
  const resp = await api.post("/plugins/scan");
  return resp.data;
}

// ── Daily Digest ──
export async function runDigest(categories: string[] = [], maxPerCat = 50, enhance = true) {
  const resp = await api.post("/tools/digest/run", {
    categories: categories.length > 0 ? categories : null,
    max_per_cat: maxPerCat,
    enhance,
  });
  return resp.data;
}

export async function listDigestDates() {
  const resp = await api.get("/tools/digest/dates");
  return resp.data.dates || [];
}

export async function getDigest(dateStr: string) {
  const resp = await api.get(`/tools/digest/${dateStr}`);
  return resp.data;
}

// ── Paper Viewer & Chat ──
export async function openPaper(arxivId: string, signal?: AbortSignal) {
  const resp = await api.post("/tools/paper/open", { arxiv_id: arxivId }, { signal });
  return resp.data;
}

export async function paperChat(arxivId: string, message: string, history: any[] = [], paperText = "", signal?: AbortSignal) {
  const resp = await api.post("/tools/paper/chat", { arxiv_id: arxivId, message, history, paper_text: paperText }, { signal });
  return resp.data;
}

export async function summarizePaper(arxivId: string, signal?: AbortSignal) {
  const resp = await api.post("/tools/paper/summarize", { arxiv_id: arxivId }, { signal });
  return resp.data;
}

// ── Settings ──
export async function getSettings() {
  const resp = await api.get("/settings");
  return resp.data;
}

export async function updateSettings(config: any) {
  const resp = await api.post("/settings", config);
  return resp.data;
}
