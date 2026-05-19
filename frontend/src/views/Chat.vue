<template>
  <div class="chat-page">
    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="chat-empty">
        <el-icon :size="48" color="#1a237e"><ChatLineSquare /></el-icon>
        <h2>AstroNova</h2>
        <p>天文学全领域 AI 科研助手</p>
        <div class="suggestions">
          <el-tag @click="sendSuggestion('搜索 arXiv 上关于中子星并合的最新论文')">🔭 搜索中子星并合</el-tag>
          <el-tag @click="sendSuggestion('帮我精读 arXiv:2301.00001')">📄 精读论文</el-tag>
          <el-tag @click="sendSuggestion('生成一张光谱图的数据可视化代码')">📊 生成图表</el-tag>
        </div>
      </div>
      <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
        <div class="msg-content">{{ msg.content }}</div>
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
        placeholder="输入你的问题..."
        @keydown.enter.exact.prevent="handleSend"
      />
      <el-button type="primary" :icon="Promotion" @click="handleSend" :disabled="!input.trim() || loading">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import { chat } from "@/api/client";
import { Promotion, ChatLineSquare } from "@element-plus/icons-vue";

const messages = ref<{ role: string; content: string }[]>([]);
const input = ref("");
const loading = ref(false);
const messagesRef = ref<HTMLElement | null>(null);

async function scrollToBottom() {
  await nextTick();
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
  }
}

async function handleSend() {
  const text = input.value.trim();
  if (!text || loading.value) return;
  input.value = "";
  messages.value.push({ role: "user", content: text });
  loading.value = true;
  await scrollToBottom();
  try {
    const resp = await chat(messages.value.map(m => ({ role: m.role, content: m.content })));
    messages.value.push({ role: "assistant", content: resp.content });
  } catch {
    messages.value.push({ role: "assistant", content: "抱歉，请求失败。请检查模型配置是否正确。" });
  } finally {
    loading.value = false;
    await scrollToBottom();
  }
}

function sendSuggestion(text: string) {
  input.value = text;
  handleSend();
}
</script>

<style scoped>
.chat-page { display: flex; flex-direction: column; height: 100%; }
.chat-messages { flex: 1; overflow-y: auto; padding: 24px; }
.chat-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 12px; color: #606266; }
.chat-empty h2 { margin: 0; font-size: 24px; color: #1a1a2e; }
.suggestions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 16px; }
.suggestions .el-tag { cursor: pointer; padding: 8px 16px; font-size: 13px; }

.msg { margin-bottom: 16px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { justify-content: flex-start; }
.msg-content { max-width: 75%; padding: 12px 16px; border-radius: 8px; line-height: 1.6; white-space: pre-wrap; }
.msg.user .msg-content { background: #1a237e; color: #fff; }
.msg.assistant .msg-content { background: #fff; color: #303133; border: 1px solid #e4e7ed; }
.thinking { color: #909399; }

.chat-input { padding: 16px 24px; background: #fff; border-top: 1px solid #e4e7ed; display: flex; gap: 12px; align-items: flex-end; }
.chat-input .el-textarea { flex: 1; }
</style>
