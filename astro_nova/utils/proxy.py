"""代理工具 — 读取环境变量代理配置，提供代理感知的 HTTP 连接

用户开着 VPN（如 Clash/V2Ray/Shadowsocks）时，这些客户端通常会在环境变量中
设置 HTTP_PROXY/HTTPS_PROXY（如 http://127.0.0.1:7890）。
本模块统一读取这些环境变量，让所有对外 HTTP 请求走代理通道。
"""

import http.client
import os
import ssl
import urllib.request
from typing import Optional
from urllib.parse import urlparse

from astro_nova.utils.logger import logger


def get_https_proxy() -> Optional[str]:
    """读取环境变量中的代理地址（优先 HTTPS_PROXY）

    如果环境变量未设置，在 Windows 上尝试读取系统代理注册表。
    """
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        val = os.environ.get(key)
        if val:
            return val.strip()

    # Windows 注册表回退：读取系统代理设置
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            ) as key:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if enabled:
                    server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    if server:
                        server = server.strip()
                        if not server.startswith("http"):
                            server = f"http://{server}"
                        return server
        except Exception:
            pass

    return None


def get_no_proxy() -> list[str]:
    """读取 NO_PROXY 环境变量 + Windows 注册表 ProxyOverride 中的豁免列表"""
    # 优先环境变量
    raw = os.environ.get("NO_PROXY") or os.environ.get("no_proxy") or ""
    items = [h.strip() for h in raw.split(",") if h.strip()]

    # Windows 注册表回退：读取系统代理豁免列表
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            ) as key:
                override, _ = winreg.QueryValueEx(key, "ProxyOverride")
                if override:
                    for item in override.split(";"):
                        item = item.strip()
                        if item and item not in items:
                            items.append(item)
        except Exception:
            pass

    return items


def _should_bypass(host: str) -> bool:
    """判断目标主机是否应该绕过代理

    支持 Windows ProxyOverride 格式的通配符:
      - 127.*       → IP 前缀匹配
      - *.example   → 域名后缀匹配
      - <local>     → 本地站点（无点号的简单主机名）
      - 192.168.*   → 匹配 192.168.x.x

    默认绕过 arXiv.org（学术资源直连更快，不受 VPN 干扰）
    """
    if host.endswith(".arxiv.org") or host == "arxiv.org":
        return True
    no_proxy = get_no_proxy()
    for exempt in no_proxy:
        if exempt == "<local>":
            if "." not in host:
                return True
            continue
        if exempt.startswith("*.") or exempt.startswith("."):
            suffix = exempt.lstrip("*.")
            if host.endswith(suffix):
                return True
        elif exempt.endswith(".*"):
            prefix = exempt[:-2]
            if host.startswith(prefix):
                return True
        elif exempt == host:
            return True
    return False


def get_proxy_components(proxy_url: Optional[str] = None) -> Optional[dict]:
    """解析代理 URL 为主机名和端口

    Returns:
        {"host": str, "port": int, "scheme": str} 或 None
    """
    proxy_url = proxy_url or get_https_proxy()
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    host = parsed.hostname
    port = parsed.port
    if not port:
        port = 443 if parsed.scheme in ("https", "socks5") else 80
    return {"host": host, "port": port, "scheme": parsed.scheme}


def create_https_connection(
    host: str,
    port: int = 443,
    timeout: int = 120,
    proxy_url: Optional[str] = None,
) -> http.client.HTTPSConnection:
    """创建 HTTPS 连接 — 自动通过代理 CONNECT 隧道

    如果环境变量中配置了 HTTPS_PROXY，则通过 HTTP 代理的 CONNECT 方法
    建立隧道连接到目标主机；否则直连。

    注意：本地代理（Clash/V2Ray）通常是 HTTP 代理，
    连接代理本身用 HTTPConnection，再通过 set_tunnel 建立 HTTPS 隧道到目标。
    """
    if _should_bypass(host):
        return http.client.HTTPSConnection(host, port, timeout=timeout)

    proxy = get_proxy_components(proxy_url)
    if proxy and proxy["host"]:
        logger.debug(
            f"通过代理 {proxy['host']}:{proxy['port']} 连接 {host}:{port}"
        )
        # 通过代理 CONNECT 隧道访问 HTTPS 目标
        # 代理本身是 HTTP 还是 HTTPS 由 proxy.scheme 决定
        context = ssl.create_default_context()
        if proxy.get("scheme") == "https":
            conn: http.client.HTTPSConnection = http.client.HTTPSConnection(
                proxy["host"], proxy["port"], timeout=timeout, context=context
            )
        else:
            conn = http.client.HTTPSConnection(
                proxy["host"], proxy["port"], timeout=timeout, context=context
            )
        conn.set_tunnel(host, port)
        return conn

    return http.client.HTTPSConnection(host, port, timeout=timeout)


def create_http_connection(
    host: str,
    port: int = 80,
    timeout: int = 120,
    proxy_url: Optional[str] = None,
) -> http.client.HTTPConnection:
    """创建 HTTP 连接 — 自动通过代理

    对于 HTTP 直连（非 HTTPS），直接通过 proxy 发起请求。
    """
    if _should_bypass(host):
        return http.client.HTTPConnection(host, port, timeout=timeout)

    proxy = get_proxy_components(proxy_url)
    if proxy and proxy["host"]:
        logger.debug(
            f"通过代理 {proxy['host']}:{proxy['port']} 连接 {host}:{port}"
        )
        return http.client.HTTPConnection(proxy["host"], proxy["port"], timeout=timeout)

    return http.client.HTTPConnection(host, port, timeout=timeout)


def get_proxy_opener() -> urllib.request.OpenerDirector:
    """创建代理感知的 urllib opener

    用于替代 urllib.request.urlopen 的默认 opener，确保走代理。
    """
    proxy_url = get_https_proxy()
    if proxy_url:
        handlers = [
            urllib.request.ProxyHandler({
                "http": proxy_url,
                "https": proxy_url,
            })
        ]
    else:
        handlers = [urllib.request.ProxyHandler({})]
    return urllib.request.build_opener(*handlers)
