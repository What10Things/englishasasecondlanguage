from __future__ import annotations

import json
import re
import socket
import ssl
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path

HOST = "englishasaforeignlanguage.com"
IP = "216.69.174.69"
PATHS = ["/", "/index.php", "/.deploy-root-check-943f6e8c3336c63b07747c4418e29e4e465798f6.txt"]


def identity(body: str) -> str:
    for pattern in (r"<title[^>]*>(.*?)</title>", r"<h1[^>]*>(.*?)</h1>"):
        match = re.search(pattern, body, flags=re.I | re.S)
        if match:
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()[:70]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    return text[:70] or "empty"


def fetch_https(path: str) -> dict[str, str | int]:
    context = ssl.create_default_context()
    conn = HTTPSConnection(HOST, 443, timeout=20, context=context)
    conn.request("GET", path, headers={"Host": HOST, "User-Agent": "EFL-vhost-check/1.0", "Cache-Control": "no-cache"})
    response = conn.getresponse()
    body = response.read().decode("utf-8", errors="replace")
    return {"status": response.status, "identity": identity(body), "server": response.getheader("Server") or ""}


def fetch_http(path: str) -> dict[str, str | int]:
    conn = HTTPConnection(IP, 80, timeout=20)
    conn.request("GET", path, headers={"Host": HOST, "User-Agent": "EFL-vhost-check/1.0", "Cache-Control": "no-cache"})
    response = conn.getresponse()
    body = response.read().decode("utf-8", errors="replace")
    return {
        "status": response.status,
        "identity": identity(body),
        "location": response.getheader("Location") or "",
        "server": response.getheader("Server") or "",
    }


results: dict[str, object] = {}
for path in PATHS:
    try:
        results[f"https:{path}"] = fetch_https(path)
    except Exception as exc:
        results[f"https:{path}"] = {"error": type(exc).__name__}
    try:
        results[f"http:{path}"] = fetch_http(path)
    except Exception as exc:
        results[f"http:{path}"] = {"error": type(exc).__name__}

try:
    context = ssl.create_default_context()
    with socket.create_connection((IP, 443), timeout=20) as raw:
        with context.wrap_socket(raw, server_hostname=HOST) as tls:
            cert = tls.getpeercert()
    sans = [value for kind, value in cert.get("subjectAltName", []) if kind == "DNS"]
    results["certificate"] = {"sans": sans[:12]}
except Exception as exc:
    results["certificate"] = {"error": type(exc).__name__}

summary_path = Path("/tmp/vhost-results.json")
summary_path.write_text(json.dumps(results, separators=(",", ":")), encoding="utf-8")
print(json.dumps(results, indent=2), flush=True)
