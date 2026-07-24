from __future__ import annotations

import os
import socket
from pathlib import Path

HOSTS = {
    "english": "englishasaforeignlanguage.com",
    "www": "www.englishasaforeignlanguage.com",
    "what10": "what10things.co.uk",
    "server": "p3plzcpnl508780.prod.phx3.secureserver.net",
}


def resolve(host: str) -> list[str]:
    addresses: list[str] = []
    try:
        for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
            address = info[4][0]
            if address not in addresses:
                addresses.append(address)
    except OSError:
        return []
    return addresses


resolved = {label: resolve(host) for label, host in HOSTS.items()}
summary = "; ".join(
    f"{label}={','.join(addresses) if addresses else 'unresolved'}"
    for label, addresses in resolved.items()
)

english = set(resolved["english"])
server = set(resolved["server"])
what10 = set(resolved["what10"])

if english and server and english & server:
    state = "success"
    message = f"DNS correct: english={','.join(resolved['english'])}; server={','.join(resolved['server'])}"
elif english and what10 and english & what10:
    state = "failure"
    message = f"DNS points with What10Things: english={','.join(resolved['english'])}; what10={','.join(resolved['what10'])}; server={','.join(resolved['server']) or 'unresolved'}"
else:
    state = "failure"
    message = f"DNS mismatch: {summary}"

print(message, flush=True)
output_path = os.environ.get("GITHUB_OUTPUT")
if output_path:
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"state={state}\n")
        output.write(f"message={message[:135]}\n")

raise SystemExit(0 if state == "success" else 1)
