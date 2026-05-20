<template>
  <div class="page">
    <div class="page-header"><h2>{{ $t('search.title') }}</h2></div>
    <div class="search-bar">
      <el-input v-model="query" :placeholder="$t('search.placeholder')" @keydown.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch" :loading="loading">{{ $t('search.search') }}</el-button>
    </div>
    <div class="search-opts">
      <el-select v-model="categories" multiple collapse-tags :placeholder="$t('search.selectCategory')" style="width:300px">
        <el-option :label="$t('search.categories.all')" value="astro-ph" />
        <el-option :label="$t('search.categories.he')" value="astro-ph.HE" />
        <el-option :label="$t('search.categories.co')" value="astro-ph.CO" />
        <el-option :label="$t('search.categories.ga')" value="astro-ph.GA" />
        <el-option :label="$t('search.categories.ep')" value="astro-ph.EP" />
        <el-option :label="$t('search.categories.sr')" value="astro-ph.SR" />
        <el-option :label="$t('search.categories.im')" value="astro-ph.IM" />
        <el-option :label="$t('search.categories.gw')" value="gr-qc" />
      </el-select>
      <el-input-number v-model="maxResults" :min="5" :max="50" size="small" />
    </div>
    <el-empty v-if="!loading && results.length === 0" :description="$t('search.empty')" />
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
          <el-button size="small" :icon="Download" @click="fetchPaperDetail(p.arxiv_id)">{{ $t('search.getFullText') }}</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { searchPapers, fetchPaper } from "@/api/client";
import { Download } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const { t } = useI18n();
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
    ElMessage.error(t('search.searchFailed'));
  } finally {
    loading.value = false;
  }
}

async function fetchPaperDetail(arxivId: string) {
  ElMessage.info(t('search.fetchingPaper'));
  try {
    const data = await fetchPaper(arxivId);
    ElMessage.success(t('search.fetchSuccess'));
  } catch {
    ElMessage.error(t('search.fetchFailed'));
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
