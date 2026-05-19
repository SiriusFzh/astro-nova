<template>
  <div class="page">
    <div class="page-header"><h2>论文库</h2></div>
    <el-empty v-if="!loading && papers.length === 0" description="还没有保存的论文，在文献搜索中保存论文" />
    <el-table v-else :data="papers" stripe style="width:100%">
      <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
      <el-table-column prop="arxiv_id" label="arXiv ID" width="120" />
      <el-table-column prop="published" label="日期" width="100" />
      <el-table-column prop="categories" label="分类" width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="80">
        <template #default="scope">
          <el-button text type="danger" :icon="Delete" @click="handleDelete(scope.row.arxiv_id)" />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { listPapers, deletePaper } from "@/api/client";
import { Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

const papers = ref<any[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try { papers.value = await listPapers(); } finally { loading.value = false; }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm("确定删除？");
    await deletePaper(id);
    ElMessage.success("已删除");
    await load();
  } catch {}
}

onMounted(load);
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
</style>
