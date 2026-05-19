<template>
  <div class="page">
    <div class="page-header">
      <h2>知识库</h2>
      <div class="header-meta">
        <el-tag v-if="storeInfo" type="info" effect="plain">
          {{ storeInfo.doc_count }} 个文档 · {{ storeInfo.sources?.length || 0 }} 个来源
        </el-tag>
      </div>
    </div>

    <div class="kb-layout">
      <!-- 左侧：搜索 -->
      <div class="kb-search">
        <div class="search-bar">
          <el-input
            v-model="query"
            placeholder="搜索知识库内容..."
            clearable
            @keydown.enter="handleSearch"
          />
          <el-button type="primary" @click="handleSearch" :loading="searching">搜索</el-button>
        </div>
        <el-empty v-if="!searching && results.length === 0 && !searched" description="输入关键词搜索知识库" />
        <div v-if="searched && results.length === 0 && !searching" class="no-results">
          <el-empty description="未找到相关内容" />
        </div>
        <div v-for="(r, i) in results" :key="i" class="result-item">
          <div class="result-header">
            <span class="result-score">得分 {{ r.score }}</span>
            <el-tag size="small" type="info">{{ r.source || '未知来源' }}</el-tag>
          </div>
          <p class="result-content">{{ r.content }}</p>
        </div>
      </div>

      <!-- 右侧：信息面板 -->
      <div class="kb-sidebar">
        <el-card shadow="never">
          <template #header>知识库状态</template>
          <div class="info-row"><span>文档块数</span><span>{{ storeInfo?.doc_count || 0 }}</span></div>
          <div class="info-row"><span>来源数量</span><span>{{ storeInfo?.sources?.length || 0 }}</span></div>
        </el-card>
        <el-card shadow="never" style="margin-top:12px">
          <template #header>来源列表</template>
          <div v-if="!storeInfo?.sources?.length" class="empty-sources">暂无数据</div>
          <div v-for="s in storeInfo?.sources || []" :key="s" class="source-item">
            <el-icon><Document /></el-icon>
            <span class="source-name">{{ s }}</span>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { knowledgeSearch, getKnowledgeInfo } from "@/api/client";
import { Document } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const query = ref("");
const searching = ref(false);
const results = ref<any[]>([]);
const searched = ref(false);
const storeInfo = ref<any>(null);

onMounted(async () => {
  try {
    storeInfo.value = await getKnowledgeInfo("default");
  } catch {
    // 知识库可能还没有数据
  }
});

async function handleSearch() {
  if (!query.value.trim()) return;
  searching.value = true;
  searched.value = true;
  try {
    const data = await knowledgeSearch(query.value, "default", 10);
    results.value = data.results || [];
  } catch {
    ElMessage.error("搜索失败");
  } finally {
    searching.value = false;
  }
}
</script>

<style scoped>
.page { padding: 24px; display: flex; flex-direction: column; height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.header-meta { display: flex; gap: 8px; }
.kb-layout { display: flex; gap: 20px; flex: 1; overflow: hidden; }
.kb-search { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }
.search-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.no-results { margin-top: 40px; }
.result-item { padding: 12px; border-radius: 8px; background: #fff; margin-bottom: 8px; border: 1px solid #ebeef5; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.result-score { font-size: 12px; color: #909399; }
.result-content { font-size: 13px; color: #303133; line-height: 1.6; margin: 0; }
.kb-sidebar { width: 280px; flex-shrink: 0; }
.info-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; color: #606266; }
.source-item { display: flex; align-items: center; gap: 6px; padding: 4px 0; font-size: 13px; color: #606266; }
.source-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-sources { color: #c0c4cc; font-size: 13px; text-align: center; padding: 12px; }
</style>
