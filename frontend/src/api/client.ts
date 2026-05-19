import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 60000,
});

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

// ── Notes ──
export async function listNotes() {
  const resp = await api.get("/notes");
  return resp.data;
}

export async function createNote(note: any) {
  const resp = await api.post("/notes", note);
  return resp.data;
}

export async function deleteNote(id: number) {
  const resp = await api.delete(`/notes/${id}`);
  return resp.data;
}

export async function generateNote(arxivId: string, title: string, content = "") {
  const resp = await api.post("/tools/note", { arxiv_id: arxivId, title, content });
  return resp.data;
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

// ── Settings ──
export async function getSettings() {
  const resp = await api.get("/settings");
  return resp.data;
}

export async function updateSettings(config: any) {
  const resp = await api.post("/settings", config);
  return resp.data;
}
