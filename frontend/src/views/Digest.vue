<template>
  <div class="page">
    <div class="page-header">
      <h2>🌌 每日 arXiv Digest</h2>
      <div class="header-actions">
        <el-select v-model="selectedDate" placeholder="选择日期" style="width:160px">
          <el-option v-for="d in dates" :key="d" :label="d" :value="d" />
        </el-select>
        <el-button type="primary" @click="loadDigest" :disabled="!selectedDate">加载</el-button>
        <el-button type="success" @click="runNewDigest" :loading="running">
          爬取今日最新
        </el-button>
      </div>
    </div>
    <p class="page-desc">
      自动爬取 arXiv 所有天文学分类的最新论文 → 去重 → LLM 生成中文摘要
    </p>

    <!-- 统计 -->
    <div v-if="papers.length > 0" class="digest-stats">
      <el-row :gutter="12">
        <el-col :span="6">
          <el-card shadow="never">
            <div class="stat-num">{{ papers.length }}</div>
            <div class="stat-label">论文总数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="stat-num">{{ stats.categories }}</div>
            <div class="stat-label">分类数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="stat-num">{{ stats.enhanced }}</div>
            <div class="stat-label">已增强</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="stat-num">{{ selectedDate || '--' }}</div>
            <div class="stat-label">日期</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 分类 Tab -->
    <div v-if="papers.length > 0" class="digest-body">
      <el-tabs v-model="activeCategory" @tab-click="switchCategory">
        <el-tab-pane
          v-for="(papersInCat, cat) in groupedPapers"
          :key="cat"
          :label="`${cat} (${papersInCat.length})`"
          :name="cat"
        >
          <div
            v-for="(p, i) in papersInCat"
            :key="p.id"
            class="paper-card"
            @click="openPaper(p)"
          >
            <div class="paper-card-header">
              <span class="paper-idx">{{ i + 1 }}</span>
              <a :href="p.abs_url" target="_blank" class="paper-title" @click.stop>
                {{ p.title }}
              </a>
              <el-tag size="small" class="paper-id">{{ p.id }}</el-tag>
            </div>
            <div class="paper-meta">
              <span class="paper-authors">{{ authorsStr(p.authors) }}</span>
            </div>
            <div v-if="p.tldr" class="paper-tldr">{{ p.tldr }}</div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-empty v-else-if="!loading && papers.length === 0" description="暂无日报，点击「爬取今日最新」开始" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { runDigest, listDigestDates, getDigest } from "@/api/client";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { useTaskStore } from "@/stores/tasks";

const router = useRouter();
const taskStore = useTaskStore();

const dates = ref<string[]>([]);
const selectedDate = ref("");
const papers = ref<any[]>([]);
const running = ref(false);
const loading = ref(false);
const activeCategory = ref("");

const CAT_NAMES: Record<string, string> = {
  "astro-ph.GA": "星系天体物理",
  "astro-ph.HE": "高能天体物理",
  "astro-ph.CO": "宇宙学",
  "astro-ph.SR": "太阳与恒星物理",
  "astro-ph.EP": "行星科学",
  "astro-ph.IM": "仪器与方法",
};

const groupedPapers = computed(() => {
  const groups: Record<string, any[]> = {};
  for (const p of papers.value) {
    const cat = p.primary_category || (p.categories?.[0]) || "其他";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(p);
  }
  return groups;
});

const stats = computed(() => {
  let enhanced = 0;
  for (const p of papers.value) {
    if (p.AI?.tldr) enhanced++;
  }
  return {
    categories: Object.keys(groupedPapers.value).length,
    enhanced,
  };
});

function authorsStr(authors: string[]): string {
  if (!authors || authors.length === 0) return "";
  return authors.slice(0, 5).join(", ") + (authors.length > 5 ? " et al." : "");
}

async function loadDates() {
  // 优先使用 Pinia 缓存（跨导航持久化）
  const cached = taskStore.digestCache;
  if (cached && cached.papers.length > 0) {
    papers.value = cached.papers;
    selectedDate.value = cached.date;
    const cats = Object.keys(groupedPapers.value);
    if (cats.length > 0) activeCategory.value = cats[0];
  }

  try {
    dates.value = await listDigestDates();
    if (dates.value.length > 0) {
      selectedDate.value = dates.value[0];
      await loadDigest();
    }
  } catch {
    dates.value = [];
  }
}

async function loadDigest() {
  if (!selectedDate.value) return;
  loading.value = true;
  try {
    const data = await getDigest(selectedDate.value);
    papers.value = data.papers || [];
    const cats = Object.keys(groupedPapers.value);
    if (cats.length > 0) activeCategory.value = cats[0];
  } catch (e: any) {
    ElMessage.error("加载失败: " + (e.message || String(e)));
    // 不重置 papers — 保留 Pinia 缓存中的数据
  } finally {
    loading.value = false;
  }
}

async function runNewDigest() {
  running.value = true;
  try {
    const result = await runDigest();
    selectedDate.value = result.date;
    // 从文件重新加载完整 paper 数据（含 AI.tldr 等完整字段）
    try {
      await loadDigest();
    } catch {
      // 回退：直接用 API 返回的数据
      papers.value = result.papers || [];
    }
    // 同步到 Pinia 缓存（跨导航持久化）
    taskStore.updateDigestCache(papers.value, result.date);
    dates.value.unshift(result.date);
    ElMessage.success(`Digest 完成: ${result.new} 篇新论文`);
  } catch (e: any) {
    ElMessage.error("Digest 失败: " + (e.message || String(e)));
  } finally {
    running.value = false;
  }
}

function switchCategory(tab: any) {
  activeCategory.value = tab.props.name;
}

function openPaper(p: any) {
  router.push(`/paper-viewer?id=${p.id}`);
}

onMounted(loadDates);
</script>

<style scoped>
.page { padding: 16px 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 6px; }
.page-header h2 { margin: 0; font-size: 18px; color: #1a1a2e; }
.header-actions { display: flex; gap: 6px; align-items: center; }
.page-desc { color: #909399; font-size: 12px; margin-bottom: 10px; }
.digest-stats { margin-bottom: 12px; }
.digest-stats :deep(.el-card__body) { padding: 10px; }
.stat-num { font-size: 20px; font-weight: 700; color: #1a237e; text-align: center; line-height: 1.2; }
.stat-label { font-size: 11px; color: #909399; text-align: center; margin-top: 2px; }
.digest-body { flex: 1; }
.digest-body :deep(.el-tabs__header) { margin-bottom: 8px; }
.digest-body :deep(.el-tabs__item) { padding: 0 12px; height: 32px; line-height: 32px; font-size: 13px; }
.paper-card {
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 4px;
  cursor: pointer;
  transition: all 0.12s;
  background: #fff;
}
.paper-card:hover { border-color: #1a237e; box-shadow: 0 1px 4px rgba(26,35,126,0.06); }
.paper-card-header { display: flex; align-items: center; gap: 6px; }
.paper-idx { width: 20px; height: 20px; background: #1a237e; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; }
.paper-title { font-size: 13px; font-weight: 500; color: #1a237e; text-decoration: none; flex: 1; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.paper-title:hover { text-decoration: underline; }
.paper-id { flex-shrink: 0; }
.paper-meta { margin: 2px 0 0 26px; }
.paper-authors { font-size: 11px; color: #909399; }
.paper-tldr { font-size: 12px; color: #303133; margin-top: 4px; margin-left: 26px; padding: 4px 8px; background: #f0f2f5; border-radius: 4px; line-height: 1.4; }
[data-theme="dark"] .page-header h2 { color: #e0e0e0; }
[data-theme="dark"] .paper-card { background: #16213e; border-color: #0f3460; }
[data-theme="dark"] .paper-title { color: #6a9eff; }
[data-theme="dark"] .paper-tldr { background: #1a2a4a; color: #e0e0e0; }
[data-theme="dark"] .stat-num { color: #6a9eff; }
</style>
