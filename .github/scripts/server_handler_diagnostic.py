from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://englishasaforeignlanguage.com"
PATHS = ["/", f"/?handler_check={int(time.time())}", "/index.php"]

results: dict[str, object] = {}
for path in PATHS:
    request = Request(
        BASE + path,
        headers={
            "User-Agent": "EFL-server-handler-check/1.0",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )
    with urlopen(request, timeout=25) as response:
        body = response.read().decode("utf-8", errors="replace")
        headers = {key.lower(): value for key, value in response.headers.items()}
        results[path] = {
            "status": response.status,
            "headers": headers,
            "what10things": "What10Things" in body,
            "efl": "EFL by Level" in body or "English that meets you" in body,
        }

Path("/tmp/server-handler-results.json").write_text(json.dumps(results), encoding="utf-8")
print(json.dumps(results, indent=2), flush=True)
