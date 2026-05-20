import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface TaskNotification {
  id: string;
  task_type: string;
  title: string;
  description: string;
  source_route: string;
  created_at: string;
}

const API_BASE = "http://127.0.0.1:8615/api/tools/tasks";

export const useTaskStore = defineStore("tasks", () => {
  // ── State ──
  const notifications = ref<TaskNotification[]>([]);
  const currentRoute = ref("");
  /** 已被用户"看过"的通知 ID（不会再出现） */
  const clearedIds = ref<string[]>([]);
  let pollTimer: number | null = null;

  // digest 缓存 — 跨导航持久化
  const digestCache = ref<{ papers: any[]; date: string } | null>(null);

  // 论文查看器缓存 — 跨导航持久化（含加载状态）
  const paperViewerCache = ref<{
    arxivId: string;
    paper: any;
    chatMessages: any[];
    loading: boolean;
  } | null>(null);

  // ── Computed ──
  /** 每个路由的未读数量（排除当前页面通知和已清除的） */
  const badgeCounts = computed(() => {
    const counts: Record<string, number> = {};
    for (const n of notifications.value) {
      if (n.source_route === currentRoute.value) continue;
      if (clearedIds.value.includes(n.id)) continue;
      counts[n.source_route] = (counts[n.source_route] || 0) + 1;
    }
    return counts;
  });

  /** 总未读数 */
  const totalBadgeCount = computed(() =>
    Object.values(badgeCounts.value).reduce((a, b) => a + b, 0),
  );

  // ── Methods ──

  /** 获取指定路由的角标数 */
  function badge(route: string): number {
    return badgeCounts.value[route] || 0;
  }

  /** 从后端拉取未读通知 */
  async function fetchNotifications() {
    try {
      const resp = await fetch(`${API_BASE}/notifications`);
      if (resp.ok) {
        const data = await resp.json();
        const remote = data.notifications || [];
        const route = currentRoute.value;

        const filtered = remote.filter((n: TaskNotification) => {
          // 已经被清除过 → 不再显示
          if (clearedIds.value.includes(n.id)) return false;
          // 当前页面的通知 → 用户已经能看到结果 → 自动清除
          if (n.source_route === route) {
            clearedIds.value.push(n.id);
            return false;
          }
          return true;
        });

        notifications.value = filtered;
      }
    } catch {
      /* backend not ready */
    }
  }

  /** 标记单条为已读 */
  async function markRead(id: string) {
    try {
      await fetch(`${API_BASE}/notifications/${id}/read`, { method: "POST" });
    } catch {}
    if (!clearedIds.value.includes(id)) clearedIds.value.push(id);
    notifications.value = notifications.value.filter((n) => n.id !== id);
  }

  /** 标记整个路由为已读（仅后端同步） */
  async function markRouteRead(route: string) {
    try {
      await fetch(
        `${API_BASE}/notifications/read-route?route=${encodeURIComponent(route)}`,
        { method: "POST" },
      );
    } catch {
      /* best effort */
    }
  }

  // ── 轮询 ──

  function startPolling() {
    fetchNotifications();
    pollTimer = window.setInterval(fetchNotifications, 5000);
  }

  function stopPolling() {
    if (pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // ── 路由变更（由 App.vue 调用） ──

  function onRouteChanged(route: string) {
    // 当前路由的所有通知 → 永久标记为已清除
    for (const n of notifications.value) {
      if (n.source_route === route && !clearedIds.value.includes(n.id)) {
        clearedIds.value.push(n.id);
      }
    }
    notifications.value = notifications.value.filter(
      (n) => n.source_route !== route,
    );
    currentRoute.value = route;
    // 后端同步（fire-and-forget）
    markRouteRead(route);
  }

  // ── Digest 缓存（跨页面导航持久化） ──

  function updateDigestCache(papers: any[], date: string) {
    digestCache.value = { papers, date };
  }

  function clearDigestCache() {
    digestCache.value = null;
  }

  // ── 论文查看器缓存（跨页面导航持久化） ──

  function updatePaperViewerCache(arxivId: string, paper: any, chatMessages: any[], loading = false) {
    paperViewerCache.value = { arxivId, paper, chatMessages, loading };
  }

  function clearPaperViewerCache() {
    paperViewerCache.value = null;
  }

  // ── 前端通知（供 Chat.vue 等组件使用） ──

  function addLocalNotification(
    taskType: string,
    title: string,
    description: string,
    sourceRoute: string,
  ) {
    const notif: TaskNotification = {
      id: `local_${Date.now()}`,
      task_type: taskType,
      title,
      description,
      source_route: sourceRoute,
      created_at: new Date().toISOString(),
    };
    // 本地通知 → 当前页面直接清除，否则显示
    if (sourceRoute === currentRoute.value) {
      clearedIds.value.push(notif.id);
    } else {
      notifications.value.push(notif);
    }
  }

  return {
    notifications,
    badgeCounts,
    totalBadgeCount,
    badge,
    digestCache,
    updateDigestCache,
    clearDigestCache,
    paperViewerCache,
    updatePaperViewerCache,
    clearPaperViewerCache,
    fetchNotifications,
    markRead,
    markRouteRead,
    startPolling,
    stopPolling,
    onRouteChanged,
    addLocalNotification,
  };
});
