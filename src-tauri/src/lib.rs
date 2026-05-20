use log::{error, info};
use std::io::Read;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::Manager;
use tauri::menu::{MenuBuilder, MenuItemBuilder};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri_plugin_shell::ShellExt;

#[cfg(windows)]
use std::os::windows::process::CommandExt;
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

struct BackendProcess {
    child: Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
    pid: Mutex<Option<u32>>,
}

fn kill_backend(pid: Option<u32>, child: Option<tauri_plugin_shell::process::CommandChild>) {
    // 1. Soft kill via CommandChild
    if let Some(c) = child {
        let _ = c.kill();
    }
    // 2. Windows — force-kill 进程树（按 PID）
    if let Some(pid) = pid {
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/T", "/PID", &pid.to_string()])
            .creation_flags(CREATE_NO_WINDOW)
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status();
    }
    // 3. 补杀 — 按进程名杀所有 astro_nova_backend.exe（防止孤儿进程）
    let _ = std::process::Command::new("taskkill")
        .args(["/F", "/IM", "astro_nova_backend.exe"])
        .creation_flags(CREATE_NO_WINDOW)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();
    // 4. 补杀 — 按进程名杀所有 backend.exe（development 模式）
    let _ = std::process::Command::new("taskkill")
        .args(["/F", "/IM", "backend.exe"])
        .creation_flags(CREATE_NO_WINDOW)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();

    std::thread::sleep(std::time::Duration::from_millis(300));
}

#[tauri::command]
fn confirm_quit(app_handle: tauri::AppHandle, state: tauri::State<BackendProcess>) -> Result<(), String> {
    info!("User confirmed quit, killing backend...");
    let child = state.child.lock().map_err(|e| format!("Lock error: {}", e))?.take();
    let pid = state.pid.lock().map_err(|e| format!("Lock error: {}", e))?.take();
    drop(state);
    kill_backend(pid, child);
    app_handle.exit(0);
    Ok(())
}

#[tauri::command]
fn open_file(path: String) -> Result<(), String> {
    std::process::Command::new("cmd")
        .args(["/c", "start", "", &path])
        .creation_flags(CREATE_NO_WINDOW)
        .spawn()
        .map_err(|e| format!("无法打开文件: {}", e))?;
    Ok(())
}

#[tauri::command]
fn export_file(src: String, dest: String) -> Result<(), String> {
    std::fs::copy(&src, &dest).map_err(|e| format!("导出失败: {}", e))?;
    Ok(())
}

fn app_config_path() -> PathBuf {
    let exe = std::env::current_exe().unwrap_or_default();
    let parent = exe.parent().unwrap_or(std::path::Path::new("."));
    parent.join("config.json")
}

fn read_config_port() -> u16 {
    let path = app_config_path();
    if let Ok(content) = std::fs::read_to_string(&path) {
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
            if let Some(port) = val.get("port").and_then(|p| p.as_u64()) {
                return port as u16;
            }
        }
    }
    8615
}

fn wait_for_backend(port: u16, max_retries: u32) -> Result<(), String> {
    let addr = format!("127.0.0.1:{}", port);
    for i in 0..max_retries {
        if let Ok(mut stream) = std::net::TcpStream::connect_timeout(
            &addr.parse().unwrap(),
            std::time::Duration::from_millis(300),
        ) {
            let request = format!("GET /api/health HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n");
            if stream.write_all(request.as_bytes()).is_ok() {
                let mut response = String::new();
                if stream.read_to_string(&mut response).is_ok()
                    && response.contains("200")
                {
                    info!("Backend ready (port {})", port);
                    return Ok(());
                }
            }
        }
        std::thread::sleep(std::time::Duration::from_millis(500));
        if i % 10 == 9 {
            info!("Waiting for backend... ({}/{})", i + 1, max_retries);
        }
    }
    Err(format!("Backend did not start within {} retries", max_retries))
}

/// 启动时清理所有残留的 backend 进程（上次异常退出留下的孤儿进程）
fn cleanup_orphaned_backends() {
    for name in &["astro_nova_backend.exe", "backend.exe"] {
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/IM", name])
            .creation_flags(CREATE_NO_WINDOW)
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status();
    }
    std::thread::sleep(std::time::Duration::from_millis(200));
}

fn setup_tray(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let show = MenuItemBuilder::with_id("show", "显示主窗口").build(app)?;
    let quit = MenuItemBuilder::with_id("quit", "退出").build(app)?;
    let menu = MenuBuilder::new(app)
        .item(&show)
        .separator()
        .item(&quit)
        .build()?;

    let icon = app.default_window_icon().cloned().ok_or("no default icon")?;

    TrayIconBuilder::new()
        .icon(icon)
        .menu(&menu)
        .tooltip("AstroNova")
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "show" => {
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                "quit" => {
                    info!("Tray quit, killing backend...");
                    if let Some(state) = app.try_state::<BackendProcess>() {
                        let child = state.child.lock().unwrap().take();
                        let pid = state.pid.lock().unwrap().take();
                        drop(state);
                        kill_backend(pid, child);
                    }
                    app.exit(0);
                }
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        })
        .build(app)?;

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(BackendProcess {
            child: Mutex::new(None),
            pid: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![open_file, export_file, confirm_quit])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // 启动前清理上次残留的 backend 进程
            cleanup_orphaned_backends();

            // 系统托盘
            if let Err(e) = setup_tray(app) {
                error!("Failed to setup tray: {}", e);
            }

            let port = read_config_port();
            let shell = app.shell();

            let (mut rx, child) = shell
                .sidecar("backend")
                .expect("Failed to create sidecar command")
                .spawn()
                .expect("Failed to spawn backend sidecar");

            let backend_pid = child.pid();
            let state = app.state::<BackendProcess>();
            *state.child.lock().unwrap() = Some(child);
            *state.pid.lock().unwrap() = Some(backend_pid);
            info!("Backend started (pid={})", backend_pid);

            // Log backend output in background thread
            std::thread::spawn(move || {
                while let Some(event) = rx.blocking_recv() {
                    match event {
                        tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                            info!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                            error!("[backend:err] {}", String::from_utf8_lossy(&line));
                        }
                        _ => {}
                    }
                }
            });

            // Wait for backend (don't block startup)
            std::thread::spawn(move || match wait_for_backend(port, 60) {
                Ok(_) => info!("Backend startup complete"),
                Err(e) => error!("{}", e),
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            info!("Shutting down backend...");
            let state = app_handle.state::<BackendProcess>();
            let child = state.child.lock().unwrap().take();
            let pid = state.pid.lock().unwrap().take();
            drop(state);
            kill_backend(pid, child);
        }
    });
}
