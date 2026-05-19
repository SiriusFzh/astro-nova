<template>
  <div class="page">
    <div class="page-header"><h2>文献搜索</h2></div>
    <div class="search-bar">
      <el-input v-model="query" placeholder="搜索关键词, 如: neutron star mergers" @keydown.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch" :loading="loading">搜索</el-button>
    </div>
    <div class="search-opts">
      <el-select v-model="categories" multiple collapse-tags placeholder="选择分类" style="width:300px">
        <el-option label="天体物理全部" value="astro-ph" />
        <el-option label="高能天体物理" value="astro-ph.HE" />
        <el-option label="宇宙学" value="astro-ph.CO" />
        <el-option label="星系与天体测量" value="astro-ph.GA" />
        <el-option label="系外行星" value="astro-ph.EP" />
        <el-option label="太阳与恒星" value="astro-ph.SR" />
        <el-option label="天文技术与仪器" value="astro-ph.IM" />
        <el-option label="引力波" value="gr-qc" />
      </el-select>
      <el-input-number v-model="maxResults" :min="5" :max="50" size="small" />
    </div>
    <el-empty v-if="!loading && results.length === 0" description="输入关键词开始搜索" />
    <el-card v-for="(p, i) in results" :key="i" class="paper-card" shadow="hover">
      <div class="paper-num">{{ i + 1 }}</div>
      <div class="paper-body">
        <h3>{{ p.title }}</h3>
        <div class="paper-meta">
          <span>arXiv: {{ p.arxiv_id }}</span>
          <span>{{ p.published }}</span>
          <el-tag size="small" v-for="cat in (p.categories || []).slice(0, 3)" :key="cat">{{ cat }}</el-tag>
        </div>
        <p class="paper-summary">{{ p.summary }}</p>
        <div class="paper-actions">
          <el-button size="small" :icon="Download" @click="fetchPaperDetail(p.arxiv_id)">获取全文</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { searchPapers, fetchPaper } from "@/api/client";
import { Download } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const query = ref("");
const categories = ref(["astro-ph"]);
const maxResults = ref(10);
const loading = ref(false);
const results = ref<any[]>([]);

async function handleSearch() {
  if (!query.value.trim()) return;
  loading.value = true;
  try {
    const data = await searchPapers(query.value, maxResults.value, categories.value);
    results.value = data.papers || [];
  } catch {
    ElMessage.error("搜索失败");
  } finally {
    loading.value = false;
  }
}

async function fetchPaperDetail(arxivId: string) {
  ElMessage.info("正在获取论文详情...");
  try {
    const data = await fetchPaper(arxivId);
    ElMessage.success("获取成功");
  } catch {
    ElMessage.error("获取失败");
  }
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.search-bar { display: flex; gap: 12px; margin-bottom: 12px; }
.search-opts { display: flex; gap: 12px; margin-bottom: 20px; align-items: center; }
.paper-card { display: flex; margin-bottom: 12px; }
.paper-num { font-size: 20px; font-weight: bold; color: #1a237e; margin-right: 16px; min-width: 30px; }
.paper-body { flex: 1; }
.paper-body h3 { margin: 0 0 8px; font-size: 15px; color: #303133; }
.paper-meta { display: flex; gap: 12px; align-items: center; font-size: 12px; color: #909399; margin-bottom: 8px; }
.paper-summary { font-size: 13px; color: #606266; line-height: 1.6; margin-bottom: 8px; }
.paper-actions { display: flex; gap: 8px; }
</style>
