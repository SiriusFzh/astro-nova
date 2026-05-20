<template>
  <div class="chat-page">
    <!-- Conversation sidebar -->
    <div class="conv-sidebar">
      <div class="conv-header">
        <span class="conv-title">对话历史</span>
        <el-button size="small" type="primary" :icon="Plus" @click="newConversation" circle />
      </div>
      <div class="conv-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conv-item', { active: conv.id === currentId }]"
          @click="switchConversation(conv.id)"
        >
          <el-icon :size="14"><ChatDotSquare /></el-icon>
          <span class="conv-name">{{ conv.title }}</span>
          <el-icon
            class="conv-del"
            :size="12"
            @click.stop="removeConversation(conv.id)"
          ><Close /></el-icon>
        </div>
        <div v-if="conversations.length === 0" class="conv-empty">暂无对话</div>
      </div>
      <!-- 快捷入口 -->
      <div class="conv-quick">
        <div class="quick-title">快捷操作</div>
        <div class="quick-item" @click="goToNotes">
          <el-icon :size="14"><Document /></el-icon>
          <span>笔记管理</span>
        </div>
      </div>
    </div>

    <!-- Chat area -->
    <div class="chat-main">
      <div class="chat-messages" ref="messagesRef">
        <div v-if="messages.length === 0 && !noProvider" class="chat-empty">
          <el-icon :size="48" color="#1a237e"><ChatLineSquare /></el-icon>
          <h2>AstroNova · NovaForge</h2>
          <p>天文学 AI 科研助手 — 输入 arXiv ID 或搜索关键词开始工作</p>
          <div class="suggestions">
            <el-tag @click="sendSuggestion('搜索 astrophysics 最新论文')">搜索论文</el-tag>
            <el-tag @click="sendSuggestion('帮我读 2301.00001 并生成笔记')">精读+笔记</el-tag>
            <el-tag @click="sendSuggestion('列出所有可用的笔记模板')">查看模板</el-tag>
          </div>
        </div>
        <!-- 未配置 Provider 引导 -->
        <div v-if="noProvider" class="chat-empty">
          <el-icon :size="48" color="#e6a23c"><WarningFilled /></el-icon>
          <h2>尚未配置 AI 模型</h2>
          <p>使用对话功能前，需要先添加一个 LLM Provider（如 DeepSeek、OpenAI、Ollama 等）。</p>
          <div class="suggestions">
            <el-button type="primary" @click="router.push('/settings/providers')">去配置模型</el-button>
          </div>
        </div>
        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <!-- Edit mode -->
          <div v-if="editingIndex === i" class="msg-edit-wrap">
            <el-input
              v-model="editText"
              type="textarea"
              :rows="3"
              @keydown.enter.exact.prevent="saveEdit(i)"
            />
            <div class="msg-edit-actions">
              <el-button size="small" type="primary" @click="saveEdit(i)">保存</el-button>
              <el-button size="small" @click="cancelEdit">取消</el-button>
            </div>
          </div>
          <!-- Normal display -->
          <template v-else>
            <div class="msg-content" v-html="renderContent(msg.content)"></div>
            <!-- Message actions (hover) -->
            <div v-if="msg.role === 'user'" class="msg-actions">
              <el-icon :size="14" title="编辑" @click="startEdit(i)"><Edit /></el-icon>
              <el-icon :size="14" title="删除" @click="confirmDeleteMsg(i)"><Delete /></el-icon>
            </div>
          </template>
          <!-- 显示笔记生成结果 -->
          <div v-if="msg.note_result" class="msg-note-result">
            <el-tag v-if="msg.note_result.pdf_available" type="success" size="small" style="cursor:pointer" @click="downloadPdf(msg.note_result.arxiv_id)">
              📄 下载 PDF
            </el-tag>
            <el-tag v-if="msg.note_result.tex_path" type="warning" size="small">
              📝 LaTeX 已保存
            </el-tag>
          </div>
        </div>
        <div v-if="loading" class="msg assistant">
          <div class="msg-content"><span class="thinking">思考中...</span></div>
        </div>
      </div>
      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          :placeholder="currentId ? '输入 arXiv ID、搜索关键词或提问...' : '请先新建或选择一个对话'"
          :disabled="!currentId"
          @keydown.enter.exact.prevent="handleSend"
        />
        <el-button type="primary" :icon="Promotion" @click="handleSend" :disabled="!input.trim() || loading || !currentId">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { chat, listConversations, createConversation, getConversation, updateConversation, deleteConversation, editMessage, deleteMessage, getNoteInfo } from "@/api/client";
import { useRouter } from "vue-router";
import { useTaskStore } from "@/stores/tasks";
import { invoke } from "@tauri-apps/api/core";
import { Promotion, ChatLineSquare, ChatDotSquare, Plus, Close, Document, Edit, Delete, WarningFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const router = useRouter();
const taskStore = useTaskStore();
const isActive = ref(true);
const API_BASE = "http://127.0.0.1:8615";
const noProvider = ref(false);

const conversations = ref<any[]>([]);
const currentId = ref<number | null>(null);
const messages = ref<any[]>([]);
const input = ref("");
const loading = ref(false);
const messagesRef = ref<HTMLElement | null>(null);
const editingIndex = ref(-1);
const editText = ref("");

async function scrollToBottom() {
  await nextTick();
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
  }
}

async function loadConversations() {
  try {
    conversations.value = await listConversations();
  } catch {
    conversations.value = [];
  }
}

async function newConversation() {
  try {
    const conv = await createConversation("新对话");
    conversations.value.unshift({ id: conv.id, title: conv.title, message_count: 0 });
    await switchConversation(conv.id);
  } catch (e) {
    console.error("创建对话失败", e);
  }
}

async function switchConversation(id: number) {
  currentId.value = id;
  try {
    const conv = await getConversation(id);
    messages.value = conv.messages || [];
  } catch {
    messages.value = [];
  }
  await scrollToBottom();
}

async function removeConversation(id: number) {
  try {
    await deleteConversation(id);
    conversations.value = conversations.value.filter(c => c.id !== id);
    if (currentId.value === id) {
      currentId.value = null;
      messages.value = [];
    }
    ElMessage.success("对话已删除");
  } catch (e: any) {
    ElMessage.error("删除失败: " + (e.response?.data?.detail || e.message));
  }
}

async function saveMessages() {
  if (!currentId.value) return;
  try {
    await updateConversation(currentId.value, { messages: messages.value });
  } catch (e) {
    console.error("保存消息失败", e);
  }
}

async function autoTitle() {
  if (!currentId.value || conversations.value.length === 0) return;
  const first = messages.value.find(m => m.role === "user");
  if (!first) return;
  const title = first.content.slice(0, 40).replace(/\n/g, " ");
  try {
    await updateConversation(currentId.value, { title });
    const found = conversations.value.find(c => c.id === currentId.value);
    if (found) found.title = title;
  } catch { /* ignore */ }
}

function renderContent(text: string): string {
  if (!text) return "";
  // Basic markdown-like rendering
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="inline-code"><code>$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    // Headers
    .replace(/^### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    // Line breaks
    .replace(/\n/g, "<br>");
  return html;
}

async function handleSend() {
  const text = input.value.trim();
  if (!text || loading.value || !currentId.value) return;

  if (conversations.value.length === 0) {
    await newConversation();
    await nextTick();
  }

  input.value = "";
  messages.value.push({ role: "user", content: text });
  await scrollToBottom();

  if (messages.value.filter(m => m.role === "user").length === 1) {
    await autoTitle();
  }

  loading.value = true;
  try {
    const resp = await chat(messages.value.map(m => ({ role: m.role, content: m.content, reasoning_content: m.reasoning_content })));
    const assistantMsg: any = { role: "assistant", content: resp.content, reasoning_content: resp.reasoning_content || undefined };

    // Detect note generation results in response
    if (resp.content.includes("笔记已保存") || resp.content.includes("PDF 已生成")) {
      const idMatch = text.match(/(\d{4}\.\d{4,5})/);
      if (idMatch) {
        assistantMsg.note_result = {
          arxiv_id: idMatch[1],
          pdf_available: true,
          tex_path: true,
        };
      }
    }

    messages.value.push(assistantMsg);
    await saveMessages();

    // 如果用户已离开此页面，触发全局通知
    if (!isActive.value) {
      taskStore.addLocalNotification("chat", "对话回复完成", text.slice(0, 50), "/chat");
    }
  } catch (e: any) {
    const detail = e.response?.data?.detail || e.message || "请求失败";
    // 检测 "no provider" 错误，显示友好引导
    if (detail.includes("没有可用的 Provider")) {
      noProvider.value = true;
      messages.value.push({
        role: "assistant",
        content: "未配置 AI 模型。请先在「设置 → 模型配置」中添加一个 Provider（如 DeepSeek、OpenAI、Ollama），然后重试。",
      });
    } else {
      messages.value.push({ role: "assistant", content: "错误: " + detail });
    }
    await saveMessages();
  } finally {
    loading.value = false;
    await scrollToBottom();
  }
}

function sendSuggestion(text: string) {
  input.value = text;
  handleSend();
}

// ── 消息编辑 / 删除 ──

function startEdit(idx: number) {
  editingIndex.value = idx;
  editText.value = messages.value[idx].content;
}

function cancelEdit() {
  editingIndex.value = -1;
  editText.value = "";
}

async function saveEdit(idx: number) {
  const text = editText.value.trim();
  if (!text || !currentId.value) return;
  try {
    await editMessage(currentId.value, idx, text);
    messages.value[idx].content = text;
    editingIndex.value = -1;
    editText.value = "";
    ElMessage.success("已修改");
  } catch (e: any) {
    ElMessage.error("修改失败: " + (e.response?.data?.detail || e.message));
  }
}

async function confirmDeleteMsg(idx: number) {
  if (!currentId.value) return;
  try {
    await ElMessage.confirm("确定删除这条消息？", "提示", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    await deleteMessage(currentId.value, idx);
    messages.value.splice(idx, 1);
    ElMessage.success("已删除");
  } catch { /* user cancelled or error */ }
}

function goToNotes() {
  router.push("/notes");
}

async function downloadPdf(arxivId: string) {
  try {
    const info = await getNoteInfo(arxivId);
    const srcPath = info?.pdf_path;
    if (!srcPath) { ElMessage.warning("PDF 文件不存在"); return; }
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({
      defaultPath: `${arxivId}_note.pdf`,
      filters: [{ name: "PDF", extensions: ["pdf"] }],
    });
    if (dest) {
      await invoke("export_file", { src: srcPath, dest });
      ElMessage.success("PDF 已保存");
    }
  } catch (e) {
    ElMessage.error("下载失败: " + String(e));
  }
}

onMounted(async () => {
  isActive.value = true;

  // 检查是否有 Provider 配置
  try {
    const resp = await fetch(`${API_BASE}/providers`);
    const providers = await resp.json();
    if (!providers || providers.length === 0) {
      noProvider.value = true;
    }
  } catch { /* backend not ready */ }

  await loadConversations();
  if (conversations.value.length > 0) {
    await switchConversation(conversations.value[0].id);
  } else {
    await newConversation();
  }
});

onUnmounted(() => {
  isActive.value = false;
});
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
  min-height: 0;
}

/* Conversation sidebar */
.conv-sidebar {
  width: 220px;
  min-width: 220px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}
.conv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}
.conv-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}
.conv-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: background 0.15s;
}
.conv-item:hover { background: #f0f2f5; }
.conv-item.active { background: #e8edf7; color: #1a237e; font-weight: 500; }
.conv-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-del { opacity: 0; transition: opacity 0.15s; color: #c0c4cc; }
.conv-del:hover { color: #f56c6c; }
.conv-item:hover .conv-del { opacity: 1; }
.conv-empty { padding: 20px; text-align: center; color: #c0c4cc; font-size: 13px; }

/* Quick actions */
.conv-quick {
  border-top: 1px solid #e4e7ed;
  padding: 8px 12px;
}
.quick-title { font-size: 12px; color: #909399; margin-bottom: 6px; }
.quick-item {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 8px; cursor: pointer; font-size: 13px;
  color: #606266; border-radius: 4px; transition: background 0.15s;
}
.quick-item:hover { background: #f0f2f5; color: #1a237e; }

/* Chat main area */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-messages { flex: 1; overflow-y: auto; padding: 24px; }
.chat-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 12px; color: #606266; }
.chat-empty h2 { margin: 0; font-size: 24px; color: #1a1a2e; }
.suggestions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 16px; }
.suggestions .el-tag { cursor: pointer; padding: 8px 16px; font-size: 13px; }

.msg { margin-bottom: 16px; display: flex; flex-direction: column; }
.msg.user { align-items: flex-end; }
.msg.assistant { align-items: flex-start; }
.msg-content { max-width: 80%; padding: 12px 16px; border-radius: 8px; line-height: 1.6; }
.msg.user .msg-content { background: #1a237e; color: #fff; }
.msg.assistant .msg-content { background: #fff; color: #303133; border: 1px solid #e4e7ed; }
.msg-actions {
  opacity: 0;
  transition: opacity 0.15s;
  display: flex;
  gap: 4px;
  margin-top: 4px;
}
.msg:hover .msg-actions { opacity: 1; }
.msg-actions .el-icon {
  cursor: pointer;
  color: #909399;
  padding: 2px;
}
.msg-actions .el-icon:hover { color: #1a237e; }
.msg-edit-wrap { max-width: 80%; width: 100%; }
.msg-edit-actions { display: flex; gap: 8px; margin-top: 6px; }
:deep(.inline-code) { background: #f0f2f5; padding: 1px 6px; border-radius: 3px; font-size: 13px; }
:deep(pre.inline-code) { background: #1e1e2e; color: #cdd6f4; padding: 12px; border-radius: 6px; overflow-x: auto; }
.thinking { color: #909399; }

.msg-note-result { margin-top: 8px; display: flex; gap: 8px; }
.msg-note-result .el-tag { cursor: pointer; }

.chat-input { padding: 16px 24px; background: #fff; border-top: 1px solid #e4e7ed; display: flex; gap: 12px; align-items: flex-end; }
.chat-input .el-textarea { flex: 1; }

/* Dark theme */
[data-theme="dark"] .conv-sidebar { background: #16213e; border-right-color: #0f3460; }
[data-theme="dark"] .conv-title { color: #e0e0e0; }
[data-theme="dark"] .conv-item { color: #b0b0c0; }
[data-theme="dark"] .conv-item:hover { background: #1a2a4a; }
[data-theme="dark"] .conv-item.active { background: #0f3460; color: #e0e0e0; }
[data-theme="dark"] .conv-quick { border-top-color: #0f3460; }
[data-theme="dark"] .conv-quick .quick-title { color: #b0b0c0; }
[data-theme="dark"] .conv-quick .quick-item { color: #b0b0c0; }
[data-theme="dark"] .conv-quick .quick-item:hover { background: #1a2a4a; color: #e0e0e0; }
[data-theme="dark"] .chat-input { background: #16213e; border-top-color: #0f3460; }
[data-theme="dark"] .msg.assistant .msg-content { background: #16213e; color: #e0e0e0; border-color: #0f3460; }
[data-theme="dark"] .chat-empty h2 { color: #e0e0e0; }
[data-theme="dark"] .chat-empty p { color: #b0b0c0; }
[data-theme="dark"] :deep(.inline-code) { background: #1a2a4a; }
[data-theme="dark"] .msg-actions .el-icon:hover { color: #6a9eff; }
</style>
