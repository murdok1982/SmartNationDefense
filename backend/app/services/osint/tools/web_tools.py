from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse

import httpx

from app.services.osint.tools.base import ToolBase, ToolResult

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"), # Link-local / Cloud metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),  # Benchmarking
    ipaddress.ip_network("240.0.0.0/4"),   # Reserved
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),      # Unique Local
    ipaddress.ip_network("fe80::/10"),     # Link-local IPv6
    ipaddress.ip_network("::ffff:0:0/96"), # IPv4-mapped IPv6
]

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.google",
    "169.254.169.254",
    "instance-data",
}

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AtalayaBot/0.1; OSINT Research)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def _is_blocked_ip(addr) -> bool:
    if hasattr(addr, "ipv4_mapped") and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_reserved
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
        or any(addr in net for net in _BLOCKED_NETWORKS)
    )


def _is_safe_url(url: str) -> bool:
    """SSRF prevention: block private/internal IPs and known internal hostnames."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        if not host:
            return False
        if host.lower() in _BLOCKED_HOSTNAMES:
            return False
        try:
            addr = ipaddress.ip_address(host)
            return not _is_blocked_ip(addr)
        except ValueError:
            # Hostname — block if it ends with .local, .internal, or .localhost
            lower = host.lower()
            if lower.endswith((".local", ".internal", ".localhost", ".localdomain")):
                return False
            return True
    except Exception:
        return False


async def is_safe_url_async(url: str) -> bool:
    """Valida la URL y resuelve DNS para bloquear IPs privadas/loopback/reservadas
    (mitiga DNS rebinding)."""
    if not _is_safe_url(url):
        return False
    host = urlparse(url).hostname or ""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    try:
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except Exception:
        return False
    if not infos:
        return False
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if _is_blocked_ip(addr):
            return False
    return True


async def _resolve_validated_ips(url: str) -> list[str]:
    """Resuelve el host y valida **todas** las IPs antes de conectar.

    Devuelve la lista de IPs públicas validadas que se usarán para fijar
    (pin) la conexión y cerrar la ventana TOCTOU de DNS rebinding.
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host:
        raise ValueError("URL blocked (SSRF protection): missing host")

    try:
        addr = ipaddress.ip_address(host)
        if _is_blocked_ip(addr):
            raise ValueError("URL blocked (SSRF protection): private address")
        return [str(addr)]
    except ValueError as exc:
        if "blocked" in str(exc):
            raise

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except Exception as exc:
        raise ValueError(f"URL blocked (SSRF protection): DNS resolution failed ({exc})") from exc

    ips: list[str] = []
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError as exc:
            raise ValueError("URL blocked (SSRF protection): invalid resolved address") from exc
        if _is_blocked_ip(addr):
            raise ValueError("URL blocked (SSRF protection): resolved to private address")
        ips.append(str(addr))
    if not ips:
        raise ValueError("URL blocked (SSRF protection): no addresses resolved")
    return ips


class _PinnedDNS:
    """Fija la resolución DNS de ``host`` a las IPs ya validadas.

    Mientras el contexto está activo, cualquier resolución de ``host``
    (incluida la que hace httpcore dentro de la petición) devuelve las IPs
    validadas, eliminando el TOCTOU entre validación y conexión.
    """

    def __init__(self, host: str, ips: list[str]):
        self.host = host.lower()
        self.ips = ips
        self._original = None

    def __enter__(self):
        self._original = socket.getaddrinfo
        original = self._original
        host_l = self.host
        ips = self.ips

        def pinned_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            name = host.decode() if isinstance(host, bytes) else host
            if isinstance(name, str) and name.lower() == host_l:
                results = []
                for ip in ips:
                    if ":" in ip:
                        results.append((socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 0, 0, 0)))
                    else:
                        results.append((socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 0)))
                return results
            return original(host, port, family, type, proto, flags)

        socket.getaddrinfo = pinned_getaddrinfo
        return self

    def __exit__(self, *exc_info):
        if self._original is not None:
            socket.getaddrinfo = self._original
        return False


async def safe_http_get(
    client: httpx.AsyncClient,
    url: str,
    headers: dict | None = None,
    max_redirects: int = 5,
) -> httpx.Response:
    """GET con validación SSRF en cada salto de redirección + IP pinning.

    La IP resuelta y validada se fija durante la petición (``_PinnedDNS``) para
    impedir DNS rebinding entre la validación y la conexión real (TASK-025).
    """
    current = url
    for _ in range(max_redirects + 1):
        if not await is_safe_url_async(current):
            raise ValueError("URL blocked (SSRF protection)")

        pinned_ips = await _resolve_validated_ips(current)
        host = urlparse(current).hostname or ""

        with _PinnedDNS(host, pinned_ips):
            resp = await client.get(current, headers=headers or _DEFAULT_HEADERS, follow_redirects=False)

        # Defensa en profundidad: el peer real debe ser una de las IPs fijadas.
        try:
            stream = resp.extensions.get("network_stream")
            server_addr = stream.get_extra_info("server_addr") if stream is not None else None
            if server_addr and str(server_addr[0]) not in pinned_ips:
                raise ValueError("URL blocked (SSRF protection): peer address mismatch")
        except ValueError:
            raise
        except Exception:
            pass

        if resp.is_redirect:
            location = resp.headers.get("location")
            if not location:
                return resp
            current = urljoin(current, location)
            continue
        return resp
    raise ValueError("Too many redirects")

class WebFetchTool(ToolBase):
    name = "web_fetch"
    description = "Fetch and extract text from public web pages"
    rate_limit_per_minute = 30

    def __init__(self, config=None) -> None:
        self.config = config

    async def execute(
        self,
        url: str,
        extract_text: bool = True,
        follow_redirects: bool = True,
        timeout: int = 30,
    ) -> ToolResult:
        if not _is_safe_url(url):
            return ToolResult(success=False, data=None, source=url, method="web_fetch", error="URL blocked (SSRF protection)")

        await self._rate_limit_check()
        t0 = time.monotonic()

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                resp = await safe_http_get(client, url, max_redirects=5 if follow_redirects else 0)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                final_url = str(resp.url)
                raw_html = resp.text

            text = ""
            title = ""
            links: list[str] = []

            if extract_text and "html" in content_type:
                try:
                    import trafilatura  # noqa: PLC0415
                    text = trafilatura.extract(raw_html) or ""
                except Exception:
                    pass

                if not text:
                    from bs4 import BeautifulSoup  # noqa: PLC0415
                    soup = BeautifulSoup(raw_html, "lxml")
                    text = soup.get_text(separator=" ", strip=True)[:10000]
                    title_tag = soup.find("title")
                    title = title_tag.get_text(strip=True) if title_tag else ""
                    links = [a.get("href", "") for a in soup.find_all("a", href=True)][:50]

            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "final_url": final_url,
                    "status_code": resp.status_code,
                    "content_type": content_type,
                    "title": title,
                    "text": text[:8000] if text else "",
                    "links": links,
                },
                source=final_url,
                method="web_fetch",
                duration_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            return ToolResult(success=False, data=None, source=url, method="web_fetch", error=str(exc))

class WebSearchTool(ToolBase):
    name = "web_search"
    description = "Public web search via DuckDuckGo"
    rate_limit_per_minute = 10

    async def execute(self, query: str, num_results: int = 10) -> ToolResult:
        await self._rate_limit_check()
        t0 = time.monotonic()
        try:
            from duckduckgo_search import DDGS  # noqa: PLC0415
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            return ToolResult(
                success=True,
                data={"query": query, "results": results},
                source="duckduckgo",
                method="web_search",
                duration_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            return ToolResult(success=False, data=None, source="duckduckgo", method="web_search", error=str(exc))

class IpGeolocationTool(ToolBase):
    name = "ip_geolocation"
    description = "Geolocation of public IP addresses"
    rate_limit_per_minute = 45

    def __init__(self, config=None) -> None:
        self.config = config

    async def execute(self, ip: str) -> ToolResult:
        await self._rate_limit_check()
        t0 = time.monotonic()

        # Validate it's not a private IP
        try:
            addr = ipaddress.ip_address(ip)
            if any(addr in net for net in _BLOCKED_NETWORKS):
                return ToolResult(success=False, data=None, source=ip, method="ip_geolocation", error="Private IP")
        except ValueError:
            return ToolResult(success=False, data=None, source=ip, method="ip_geolocation", error="Invalid IP")

        url = f"https://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,asname"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            if data.get("status") == "fail":
                return ToolResult(success=False, data=None, source=url, method="ip_geolocation", error=data.get("message", ""))

            return ToolResult(
                success=True,
                data=data,
                source=url,
                method="ip_geolocation",
                duration_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            return ToolResult(success=False, data=None, source=url, method="ip_geolocation", error=str(exc))
