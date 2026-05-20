<template>
  <div class="page">
    <div class="page-header"><h2>{{ $t('settings.skills.title') }}</h2></div>
    <p class="page-desc">{{ $t('settings.skills.desc') }}</p>

    <el-empty v-if="loading && skills.length === 0" :description="$t('settings.skills.loading')" />
    <div v-for="s in skills" :key="s.name" class="skill-card">
      <div class="skill-header">
        <div class="skill-info">
          <span class="skill-name">{{ s.name }}</span>
          <span class="skill-desc">{{ s.description }}</span>
        </div>
        <el-switch
          :model-value="s.is_active"
          @change="(val: boolean) => toggle(s.name, val)"
          :active-text="$t('settings.skills.active')"
          :inactive-text="$t('settings.skills.inactive')"
        />
      </div>
      <div class="skill-body" v-if="s.is_active">
        <div class="skill-triggers" v-if="s.triggers?.length">
          <el-tag size="small" v-for="t in s.triggers" :key="t" type="info" effect="plain">{{ t }}</el-tag>
        </div>
        <el-input
          v-model="s.prompt_preview"
          type="textarea"
          :rows="4"
          readonly
          class="skill-prompt"
        />
      </div>
    </div>

    <el-empty v-if="!loading && skills.length === 0" :description="$t('settings.skills.empty')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { getSkills, toggleSkill } from "@/api/client";
import { ElMessage } from "element-plus";

const { t } = useI18n();
const skills = ref<any[]>([]);
const loading = ref(false);

onMounted(async () => {
  loading.value = true;
  try {
    const data = await getSkills();
    skills.value = data.skills || [];
  } catch {
    ElMessage.error(t('settings.skills.fetchFailed'));
  } finally {
    loading.value = false;
  }
});

async function toggle(name: string, active: boolean) {
  try {
    await toggleSkill(name, active);
    const s = skills.value.find((x) => x.name === name);
    if (s) s.is_active = active;
    ElMessage.success(active ? t('settings.skills.toggleActive') : t('settings.skills.toggleInactive'));
  } catch {
    ElMessage.error(t('settings.skills.toggleFailed'));
  }
}
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1a1a2e; }
.page-desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.skill-card { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.skill-header { display: flex; justify-content: space-between; align-items: center; }
.skill-info { display: flex; flex-direction: column; gap: 4px; }
.skill-name { font-weight: 600; font-size: 15px; color: #303133; }
.skill-desc { font-size: 12px; color: #909399; }
.skill-body { margin-top: 12px; }
.skill-triggers { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.skill-prompt { font-size: 12px; }
</style>
