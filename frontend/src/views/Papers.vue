<template>
  <div class="page">
    <div class="page-header"><h2>{{ $t('papers.title') }}</h2></div>
    <el-empty v-if="!loading && papers.length === 0" :description="$t('papers.empty') + '，' + $t('papers.saveFromSearch')" />
    <el-table v-else :data="papers" stripe style="width:100%">
      <el-table-column prop="title" :label="$t('papers.tableTitle')" min-width="300" show-overflow-tooltip />
      <el-table-column prop="arxiv_id" :label="$t('papers.tableArxivId')" width="120" />
      <el-table-column prop="published" :label="$t('papers.tableDate')" width="100" />
      <el-table-column prop="categories" :label="$t('papers.tableCategories')" width="200" show-overflow-tooltip />
      <el-table-column :label="$t('papers.tableActions')" width="80">
        <template #default="scope">
          <el-button text type="danger" :icon="Delete" @click="handleDelete(scope.row.arxiv_id)" />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { listPapers, deletePaper } from "@/api/client";
import { Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

const { t } = useI18n();
const papers = ref<any[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try { papers.value = await listPapers(); } finally { loading.value = false; }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm(t('papers.deleteConfirm'));
    await deletePaper(id);
    ElMessage.success(t('papers.deleted'));
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
