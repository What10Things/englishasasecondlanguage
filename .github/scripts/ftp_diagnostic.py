from __future__ import annotations

import ftplib
import os
import socket
from pathlib import Path


def finish(state: str, message: str) -> int:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"state={state}\n")
            output.write(f"message={message}\n")
    print(message, flush=True)
    return 0 if state == "success" else 1


def test_host(host: str, username: str, password: str, server_dir: str) -> str:
    try:
        socket.getaddrinfo(host, 21)
        with socket.create_connection((host, 21), timeout=12):
            pass
    except OSError:
        return "unreachable"

    try:
        with ftplib.FTP_TLS(timeout=25) as ftp:
            ftp.connect(host, 21)
            ftp.auth()
            ftp.prot_p()
            ftp.login(username, password)

            target = server_dir
            if target not in {".", "./", "/"}:
                target = target.removeprefix("./").rstrip("/")
                try:
                    ftp.cwd(target)
                except ftplib.error_perm:
                    return "bad-directory"
            ftp.pwd()
        return "success"
    except ftplib.error_perm as exc:
        return "bad-login" if str(exc).startswith("530") else "rejected"
    except (ftplib.Error, OSError, EOFError):
        return "tls-failure"


server = os.environ.get("FTP_SERVER", "").strip()
username = os.environ.get("FTP_USERNAME", "").strip()
password = os.environ.get("FTP_PASSWORD", "")
server_dir = os.environ.get("FTP_SERVER_DIR", "").strip()

if not all((server, username, password, server_dir)):
    raise SystemExit(finish("failure", "One or more required FTP secrets are missing"))

if "://" in server or "/" in server:
    raise SystemExit(finish("failure", "FTP_SERVER must be a hostname only, with no protocol or path"))

candidates = []
for candidate in (server, "englishasaforeignlanguage.com", "ftp.englishasaforeignlanguage.com"):
    if candidate not in candidates:
        candidates.append(candidate)

results = {candidate: test_host(candidate, username, password, server_dir) for candidate in candidates}

if results[server] == "success":
    raise SystemExit(finish("success", "FTPS hostname, login and target directory are valid"))

for candidate in candidates[1:]:
    if results[candidate] == "success":
        raise SystemExit(finish("failure", f"Change FTP_SERVER to {candidate}"))

current = results[server]
if current == "bad-login":
    message = "FTP username or password was rejected by GoDaddy"
elif current == "bad-directory":
    message = "FTP login works, but FTP_SERVER_DIR is not accessible"
elif current == "tls-failure":
    message = "GoDaddy FTPS/TLS connection could not be established"
elif current == "rejected":
    message = "GoDaddy rejected the FTPS request"
else:
    message = "FTP_SERVER could not be reached; use the cPanel Shared IP Address or FTP host"

raise SystemExit(finish("failure", message))
