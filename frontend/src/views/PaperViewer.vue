<template>
  <div class="paper-viewer">
    <!-- 顶部栏 -->
    <div class="viewer-topbar">
      <div class="topbar-left">
        <el-input
          v-model="arxivInput"
          placeholder="输入 arXiv ID (如 2301.00001)"
          style="width:220px"
          clearable
          @keydown.enter="open"
        />
        <el-button type="primary" @click="open" :loading="loading">打开</el-button>
        <el-button v-if="paper.title" @click="summarize" :loading="summarizing">总结</el-button>
      </div>
      <div class="topbar-right">
        <a v-if="paper.abs_url" :href="paper.abs_url" target="_blank" class="topbar-link">arXiv 页面</a>
        <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" class="topbar-link">PDF</a>
      </div>
    </div>

    <!-- 分割面板 -->
    <div class="viewer-split" v-if="paper.title">
      <!-- 左：论文内容 -->
      <div class="split-left">
        <div class="paper-info">
          <h2 class="paper-title">{{ paper.title }}</h2>
          <p class="paper-authors">{{ authorsStr(paper.authors) }}</p>
          <p class="paper-meta">
            <el-tag size="small">{{ paper.arxiv_id }}</el-tag>
            <el-tag v-if="paper.source" size="small" type="info">{{ paper.source }}</el-tag>
          </p>
        </div>

        <el-tabs v-model="leftTab" class="paper-tabs">
          <el-tab-pane label="全文" name="text">
            <div class="paper-text" ref="paperTextRef">
              <div v-for="(sec, i) in paper.sections" :key="i" :id="`sec-${i}`" class="paper-section">
                <h3 class="sec-heading">{{ sec.heading }}</h3>
                <p class="sec-text">{{ sec.text }}</p>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="PDF 预览" name="pdf">
            <iframe
              v-if="paper.pdf_url"
              class="pdf-iframe"
              :src="`https://arxiv.org/pdf/${paper.arxiv_id}`"
              frameborder="0"
            ></iframe>
            <el-empty v-else description="PDF 不可用" />
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右：聊天面板 -->
      <div class="split-right">
        <div class="chat-panel">
          <div class="chat-header">
            <span>论文问答</span>
            <el-tooltip content="AI 回答会标注引用来源 [Sec-N]，点击可定位到原文" placement="top">
              <el-icon :size="16" color="#909399"><InfoFilled /></el-icon>
            </el-tooltip>
          </div>

          <div class="chat-messages" ref="chatMessagesRef">
            <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.role]">
              <div class="chat-msg-content" v-html="renderChatMsg(msg)"></div>
              <!-- 引用气泡 -->
              <div v-if="msg.citations && msg.citations.length > 0" class="chat-citations">
                <div
                  v-for="(c, j) in msg.citations"
                  :key="j"
                  class="citation-chip"
                  @click="scrollToSection(c.sec)"
                >
                  <el-icon :size="12"><Link /></el-icon>
                  {{ c.headheading || `[Sec-${c.sec}]` }}
                </div>
              </div>
            </div>
            <div v-if="chatLoading" class="chat-msg assistant">
              <div class="chat-msg-content thinking">思考中...</div>
            </div>
          </div>

          <div class="chat-input">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="3"
              placeholder="问关于论文的问题...例如: 总结这篇论文 / 这个方法有什么创新？ / 用英文解释这个结论"
              @keydown.enter.exact.prevent="sendChat"
            />
            <el-button type="primary" @click="sendChat" :disabled="!chatInput.trim() || chatLoading">
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="viewer-empty">
      <el-icon :size="48" color="#909399"><View /></el-icon>
      <h3>论文查看器</h3>
      <p>输入 arXiv ID，一键打开论文。右侧聊天面板支持提问、总结、溯源引用。</p>
      <div class="empty-suggestions">
        <el-tag v-for="sid in suggestions" :key="sid" @click="arxivInput = sid; open()">
          {{ sid }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { openPaper, paperChat, summarizePaper } from "@/api/client";
import { ElMessage } from "element-plus";
import { InfoFilled, Link, View } from "@element-plus/icons-vue";
import { useTaskStore } from "@/stores/tasks";

const route = useRoute();
const taskStore = useTaskStore();

const arxivInput = ref("");
const paper = ref<any>({});
const loading = ref(false);
const summarizing = ref(false);
const leftTab = ref("text");
const chatInput = ref("");
const chatMessages = ref<any[]>([]);
const chatLoading = ref(false);
const chatMessagesRef = ref<HTMLElement | null>(null);

const suggestions = ["2301.00001", "2303.18223", "2305.16213", "2401.00999"];

function authorsStr(authors: string[]): string {
  if (!authors) return "";
  return authors.slice(0, 8).join(", ") + (authors.length > 8 ? " et al." : "");
}

function renderChatMsg(msg: any): string {
  if (!msg.content) return "";
  let html = msg.content
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
  // Highlight citations
  html = html.replace(/\[Sec-(\d+)\]/g, '<a href="javascript:void(0)" onclick="scrollToSec($1)" class="citation-link">[Sec-$1]</a>');
  return html;
}

async function open() {
  const id = parseId(arxivInput.value);
  if (!id) { ElMessage.warning("请输入 arXiv ID"); return; }

  loading.value = true;
  paper.value = {};
  chatMessages.value = [];
  // 立即缓存加载状态 — 切换页面再回来能恢复
  taskStore.updatePaperViewerCache(id, null, [], true);

  try {
    const result = await openPaper(id);
    if (result.error) { ElMessage.error(result.error); return; }
    if (!result.title) {
      ElMessage.warning("论文元数据获取成功但标题为空，可能为 arXiv 格式不兼容");
      paper.value = result;
    } else {
      paper.value = result;
      // 缓存最终结果（即使组件已销毁，Pinia 持久化）
      taskStore.updatePaperViewerCache(id, result, [], false);
      ElMessage.success("论文已加载");
    }
  } catch (e: any) {
    ElMessage.error("打开失败: " + (e.message || String(e)));
  } finally {
    loading.value = false;
  }
}

function parseId(input: string): string {
  const s = input.trim();
  const m = s.match(/(\d{4}\.\d{4,5})(v\d+)?/);
  return m ? m[1] : s;
}

async function sendChat() {
  const text = chatInput.value.trim();
  if (!text || chatLoading.value || !paper.value.arxiv_id) return;

  chatInput.value = "";
  chatMessages.value.push({ role: "user", content: text });
  chatLoading.value = true;

  try {
    const result = await paperChat(
      paper.value.arxiv_id,
      text,
      chatMessages.value.map(m => ({ role: m.role, content: m.content })).slice(-10),
      paper.value.text || "",
    );
    chatMessages.value.push({
      role: "assistant",
      content: result.answer || "（空回复）",
      citations: result.citations || [],
    });
  } catch (e: any) {
    chatMessages.value.push({ role: "assistant", content: "错误: " + (e.message || String(e)) });
  } finally {
    // 更新缓存中的聊天记录
    taskStore.updatePaperViewerCache(paper.value.arxiv_id, paper.value, chatMessages.value);
    chatLoading.value = false;
    await scrollChat();
  }
}

async function summarize() {
  if (!paper.value.arxiv_id) return;
  summarizing.value = true;
  try {
    const result = await summarizePaper(paper.value.arxiv_id);
    chatMessages.value.push({
      role: "assistant",
      content: result.answer || "总结完成",
      citations: result.citations || [],
    });
    await scrollChat();
    ElMessage.success("总结完成");
  } catch (e: any) {
    ElMessage.error("总结失败: " + (e.message || String(e)));
  } finally {
    summarizing.value = false;
  }
}

function scrollToSection(secIdx: number) {
  leftTab.value = "text";
  nextTick(() => {
    const el = document.getElementById(`sec-${secIdx}`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

async function scrollChat() {
  await nextTick();
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
  }
}

// Handle citation clicks from v-html
(window as any).scrollToSec = (secIdx: number) => scrollToSection(secIdx);

onMounted(() => {
  // 优先从 Pinia 缓存恢复
  const cached = taskStore.paperViewerCache;
  if (cached) {
    arxivInput.value = cached.arxivId;
    if (cached.paper?.arxiv_id) {
      // 有论文数据 → 恢复
      paper.value = cached.paper;
      chatMessages.value = cached.chatMessages || [];
      return;
    }
    if (cached.loading && cached.arxivId) {
      // 还在加载中 → 显示加载状态，等 1 秒后检查是否已完成
      loading.value = true;
      setTimeout(() => {
        const recheck = taskStore.paperViewerCache;
        if (recheck?.paper?.arxiv_id) {
          paper.value = recheck.paper;
          chatMessages.value = recheck.chatMessages || [];
          loading.value = false;
        } else {
          // 后台请求可能已失败或中断 → 重新加载
          open();
        }
      }, 1000);
      return;
    }
  }

  const id = route.query.id as string;
  if (id) {
    arxivInput.value = id;
    open();
  }
});
</script>

<style scoped>
.paper-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Top bar */
.viewer-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}
.topbar-left, .topbar-right { display: flex; align-items: center; gap: 8px; }
.topbar-link { font-size: 13px; color: #1a237e; text-decoration: none; }
.topbar-link:hover { text-decoration: underline; }

/* Split panel */
.viewer-split {
  display: flex;
  flex: 1;
  min-height: 0;
}
.split-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
  overflow: hidden;
}
.split-right {
  width: 400px;
  min-width: 350px;
  display: flex;
  flex-direction: column;
}

/* Paper content */
.paper-info { padding: 16px; border-bottom: 1px solid #e4e7ed; }
.paper-title { margin: 0 0 8px; font-size: 18px; color: #1a1a2e; }
.paper-authors { font-size: 13px; color: #606266; margin: 0 0 8px; }
.paper-meta { display: flex; gap: 6px; }
.paper-tabs { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.paper-tabs :deep(.el-tabs) { height: 100%; display: flex; flex-direction: column; }
.paper-tabs :deep(.el-tabs__content) { flex: 1; overflow: hidden; min-height: 0; }
.paper-tabs :deep(.el-tab-pane) { height: 100%; overflow-y: auto; }
.paper-text { padding: 16px; }
.paper-section { margin-bottom: 16px; }
.sec-heading { font-size: 15px; color: #1a237e; margin: 0 0 8px; }
.sec-text { font-size: 13px; line-height: 1.7; color: #303133; margin: 0; white-space: pre-wrap; }
.pdf-iframe { width: 100%; height: 100%; border: none; }

/* Chat panel */
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.chat-header {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px; font-weight: 600; font-size: 14px;
  border-bottom: 1px solid #e4e7ed; color: #303133;
}
.chat-messages { flex: 1; overflow-y: auto; padding: 12px; }
.chat-msg { margin-bottom: 12px; }
.chat-msg.user { text-align: right; }
.chat-msg-content {
  display: inline-block;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  text-align: left;
  max-width: 100%;
  white-space: pre-wrap;
}
.chat-msg.user .chat-msg-content { background: #1a237e; color: #fff; }
.chat-msg.assistant .chat-msg-content { background: #f0f2f5; color: #303133; }
.thinking { color: #909399; }
.chat-citations { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; }
.citation-chip {
  font-size: 11px; padding: 2px 8px;
  background: #e8edf7; color: #1a237e; border-radius: 12px;
  cursor: pointer; display: flex; align-items: center; gap: 3px;
}
.citation-chip:hover { background: #d0d9f0; }
:deep(.citation-link) { color: #1a237e; font-weight: 600; cursor: pointer; text-decoration: underline; }

.chat-input { padding: 12px; border-top: 1px solid #e4e7ed; display: flex; gap: 8px; align-items: flex-end; }
.chat-input .el-textarea { flex: 1; }

/* Empty state */
.viewer-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 12px; color: #606266; padding: 40px; }
.viewer-empty h3 { margin: 0; font-size: 18px; color: #303133; }
.empty-suggestions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 12px; }
.empty-suggestions .el-tag { cursor: pointer; }

/* Dark theme */
[data-theme="dark"] .viewer-topbar { background: #16213e; border-bottom-color: #0f3460; }
[data-theme="dark"] .split-left { border-right-color: #0f3460; }
[data-theme="dark"] .paper-title { color: #e0e0e0; }
[data-theme="dark"] .paper-authors { color: #b0b0c0; }
[data-theme="dark"] .sec-text { color: #e0e0e0; }
[data-theme="dark"] .chat-header { border-bottom-color: #0f3460; color: #e0e0e0; }
[data-theme="dark"] .chat-msg.assistant .chat-msg-content { background: #1a2a4a; color: #e0e0e0; }
[data-theme="dark"] .citation-chip { background: #0f3460; color: #6a9eff; }
[data-theme="dark"] .chat-input { border-top-color: #0f3460; }
[data-theme="dark"] .viewer-empty h3 { color: #e0e0e0; }
[data-theme="dark"] :deep(.citation-link) { color: #6a9eff; }
</style>
