const { app, BrowserWindow, Tray, Menu, nativeImage, dialog, Notification } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");
const { autoUpdater } = require("electron-updater");

const PORT = 8615;
const BACKEND_URL = `http://127.0.0.1:${PORT}`;

let mainWindow = null;
let tray = null;
let pythonProcess = null;

// ── 图标 ─────────────────────────────────────────────────────────────
function getIconPath() {
  const buildIcon = path.join(__dirname, "..", "build", "icon.png");
  if (fs.existsSync(buildIcon)) return buildIcon;
  return path.join(__dirname, "..", "build", "icon.png");
}

function getTrayIcon() {
  const p = getIconPath();
  if (!fs.existsSync(p)) return nativeImage.createEmpty();
  // Windows 托盘需要 32x32 或 16x16
  return nativeImage.createFromPath(p).resize({ width: 32, height: 32 });
}

// ── Python 后端 ──────────────────────────────────────────────────────
function getPythonPath() {
  const bundled = path.join(process.resourcesPath, "backend", "astro_nova_backend.exe");
  if (fs.existsSync(bundled)) return bundled;
  return process.platform === "win32" ? "python" : "python3";
}

function startBackend() {
  const pythonPath = getPythonPath();
  const isDev = !app.isPackaged;

  // 生产模式下，后端代码在 resources/backend/ 下
  // 用 python -m astro_nova 启动，cwd 指向 backend 目录
  const backendDir = isDev
    ? path.join(__dirname, "..")
    : path.join(process.resourcesPath, "backend");

  const args = ["-m", "astro_nova"];
  const cwd = backendDir;

  console.log(`[main] 启动后端: ${pythonPath} ${args.join(" ")} (cwd=${cwd})`);
  pythonProcess = spawn(pythonPath, args, {
    cwd,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });
  pythonProcess.stdout.on("data", (d) => console.log(`[backend] ${d.toString().trim()}`));
  pythonProcess.stderr.on("data", (d) => console.error(`[backend:err] ${d.toString().trim()}`));
  pythonProcess.on("exit", (code) => {
    console.log(`[main] 后端退出 (code=${code})`);
    pythonProcess = null;
  });
}

function stopBackend() {
  if (!pythonProcess) return;
  console.log("[main] 停止后端...");
  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(pythonProcess.pid), "/f", "/t"]);
  } else {
    pythonProcess.kill("SIGTERM");
  }
  pythonProcess = null;
}

function waitForBackend(retries = 30) {
  return new Promise((resolve, reject) => {
    const check = (n) => {
      if (n <= 0) return reject(new Error("后端启动超时"));
      http.get(`${BACKEND_URL}/api/health`, (res) => {
        res.statusCode === 200 ? resolve() : setTimeout(() => check(n - 1), 1000);
      }).on("error", () => setTimeout(() => check(n - 1), 1000));
    };
    check(retries);
  });
}

// ── 主窗口 ─────────────────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "AstroNova",
    icon: getIconPath(),
    show: false,                          // 等后端就绪后再显示
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // 关闭 → 隐藏到托盘（不退出）
  mainWindow.on("close", (e) => {
    if (app.isQuitting) return;           // 真正退出时放行
    if (tray) {
      e.preventDefault();
      mainWindow.hide();
      // 可选: 显示通知
      if (Notification.isSupported()) {
        const notif = new Notification({ title: "AstroNova", body: "已最小化到系统托盘" });
        notif.show();
      }
    }
    // 没有托盘时直接退出
  });

  mainWindow.on("ready-to-show", () => mainWindow.show());
}

// ── 系统托盘 ──────────────────────────────────────────────────────────
function createTray() {
  tray = new Tray(getTrayIcon());
  tray.setToolTip("AstroNova — 天文学科研助手");

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "显示窗口",
      click: () => { mainWindow?.show(); mainWindow?.focus(); },
    },
    { type: "separator" },
    {
      label: "关于 AstroNova",
      click: () => { dialog.showMessageBox({ type: "info", title: "AstroNova", message: "AstroNova v1.0.0\n天文学科研助手桌面客户端" }); },
    },
    { type: "separator" },
    {
      label: "退出",
      click: () => {
        app.isQuitting = true;
        stopBackend();
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on("double-click", () => { mainWindow?.show(); mainWindow?.focus(); });
}

// ── 自动更新 ────────────────────────────────────────────────────────
function setupAutoUpdater() {
  if (!app.isPackaged) return;

  autoUpdater.autoDownload = false;
  autoUpdater.setFeedURL({
    provider: "github",
    owner: "SiriusFzh",
    repo: "astro-nova",
  });

  autoUpdater.on("update-available", (info) => {
    dialog.showMessageBox({
      type: "info",
      title: "发现新版本",
      message: `AstroNova ${info.version} 可用`,
      detail: "是否下载更新？下载完成后将提示安装。",
      buttons: ["下载", "稍后"],
      defaultId: 0,
      cancelId: 1,
    }).then(({ response }) => {
      if (response === 0) autoUpdater.downloadUpdate();
    });
  });

  autoUpdater.on("update-downloaded", () => {
    dialog.showMessageBox({
      type: "info",
      title: "更新已下载",
      message: "更新已下载完成，是否立即重启安装？",
      buttons: ["立即重启", "稍后"],
      defaultId: 0,
      cancelId: 1,
    }).then(({ response }) => {
      if (response === 0) autoUpdater.quitAndInstall();
    });
  });

  autoUpdater.on("error", (err) => {
    console.error("[autoUpdater]", err.message);
  });

  setTimeout(() => autoUpdater.checkForUpdates(), 3000);
}

// ── 应用生命周期 ──────────────────────────────────────────────────────
app.whenReady().then(async () => {
  startBackend();

  try {
    await waitForBackend();
    console.log("[main] 后端已就绪");
  } catch (e) {
    dialog.showErrorBox("启动失败", `无法连接到后端服务 (port ${PORT})\n${e.message}`);
    stopBackend();
    app.quit();
    return;
  }

  createTray();
  createWindow();
});

// 所有窗口关闭 → 不退出（有托盘时由 close 事件接管）
app.on("window-all-closed", (e) => {
  if (tray) {
    // 有托盘时保留进程
  } else {
    if (process.platform !== "darwin") app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow) mainWindow.show();
});

app.on("before-quit", () => {
  app.isQuitting = true;
  stopBackend();
});

// 托盘需要在退出前销毁，否则 Windows 上图标残留
app.on("will-quit", () => {
  if (tray) { tray.destroy(); tray = null; }
});
