from __future__ import annotations

import csv
import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from flask import Flask, Response, jsonify, redirect, request, send_from_directory

APP_ROOT = Path(__file__).resolve().parent
LOGGER = logging.getLogger("efl")

# Formula-injection guard: Excel/Sheets treat leading =, +, -, @ as formulas.
FORMULA_TRIGGERS = ("=", "+", "-", "@")

# Simple in-process rate limit for the form endpoint: max requests per window per IP.
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_lock = Lock()
_rate_limit_hits: dict[str, deque[float]] = {}


def sanitise_csv_field(value: str) -> str:
    if value and value[0] in FORMULA_TRIGGERS:
        return "'" + value
    return value


def is_rate_limited(key: str) -> bool:
    now = time.monotonic()
    with _rate_limit_lock:
        hits = _rate_limit_hits.setdefault(key, deque())
        while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_MAX_REQUESTS:
            return True
        hits.append(now)
        return False


def normalise_path(value: str) -> str:
    path = "/" + value.lstrip("/")
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


def load_or_create_secret_key() -> str:
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_file = APP_ROOT / "storage" / ".secret_key"
    try:
        existing = key_file.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except OSError:
        pass
    generated = os.urandom(32).hex()
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(key_file.parent, 0o700)
        fd = os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(generated)
    except OSError:
        LOGGER.warning("Could not persist generated SECRET_KEY; a new one will be created on next boot")
    return generated


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder="assets", static_url_path="/assets")
    app.config.from_mapping(
        SECRET_KEY=load_or_create_secret_key(),
        PAGES_DIR=str(APP_ROOT / "pages"),
        PUBLIC_DIR=str(APP_ROOT / "public"),
        MANIFEST_PATH=str(APP_ROOT / "page_manifest.json"),
        SUBMISSIONS_PATH=str(APP_ROOT / "storage" / "submissions.csv"),
        SUBMISSION_RETENTION_DAYS=int(os.environ.get("SUBMISSION_RETENTION_DAYS", "730")),
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    try:
        manifest = json.loads(Path(app.config["MANIFEST_PATH"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.error("Failed to load page manifest from %s: %s", app.config["MANIFEST_PATH"], exc)
        manifest = {}

    def page_response(path: str, status: int = 200) -> Response:
        route = normalise_path(path)
        filename = manifest.get(route) or manifest.get(route.rstrip("/"))
        if not filename:
            filename = manifest.get("/404/") or manifest.get("/404")
            status = 404
        if not filename:
            return Response(
                "<!doctype html><title>Page not found | EFL by Level</title>"
                "<h1>Page not found</h1><p><a href='/'>Return home</a></p>",
                status=404,
                mimetype="text/html",
            )
        try:
            html = (Path(app.config["PAGES_DIR"]) / filename).read_text(encoding="utf-8")
        except OSError as exc:
            LOGGER.error("Failed to read page %s for route %s: %s", filename, route, exc)
            return Response("Page unavailable", status=503, mimetype="text/plain")
        return Response(html, status=status, mimetype="text/html")

    def prune_submissions(output: Path, now: datetime) -> None:
        if not output.exists() or output.stat().st_size == 0:
            return
        cutoff = now - timedelta(days=int(app.config["SUBMISSION_RETENTION_DAYS"]))
        with output.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames
            rows = list(reader)
        if not fieldnames:
            return
        kept = []
        for row in rows:
            try:
                created = datetime.fromisoformat(row.get("created_at", ""))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                kept.append(row)
                continue
            if created >= cutoff:
                kept.append(row)
        if len(kept) == len(rows):
            return
        temporary = output.with_suffix(".tmp")
        with temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept)
        temporary.replace(output)

    def save_submission(path: str) -> tuple[bool, str]:
        values = request.get_json(silent=True) if request.is_json else request.form.to_dict(flat=True)
        values = values or {}
        allowed = {"email", "name", "first_name", "source", "message", "level", "privacy_ack", "marketing_consent"}
        safe_values = {
            str(key): str(value)[:5000]
            for key, value in values.items()
            if str(key) in allowed
        }
        email = safe_values.get("email", "").strip().lower()[:254]
        name = safe_values.get("name", safe_values.get("first_name", "")).strip()[:120]
        if not name or "@" not in email or safe_values.get("privacy_ack") != "yes":
            return False, "Please complete the required details and privacy acknowledgement."
        name = sanitise_csv_field(name)
        output = Path(app.config["SUBMISSIONS_PATH"])
        output.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        prune_submissions(output, now)
        new_file = not output.exists()
        with output.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["created_at", "path", "email", "name", "consent", "payload"])
            if new_file:
                writer.writeheader()
            writer.writerow(
                {
                    "created_at": now.isoformat(),
                    "path": path[:200],
                    "email": email,
                    "name": name,
                    "consent": sanitise_csv_field(safe_values.get("marketing_consent", "")[:40]),
                    "payload": json.dumps(safe_values, ensure_ascii=False, sort_keys=True),
                }
            )
        return True, "Thank you. Your details have been received."

    @app.get("/health")
    def health():
        status = "ok" if manifest else "degraded"
        return jsonify(status=status, runtime="flask", pages=len(manifest), application="EFL by Level")

    @app.route("/", methods=["GET", "HEAD", "POST"])
    @app.route("/<path:requested_path>", methods=["GET", "HEAD", "POST"])
    def dispatch(requested_path: str = ""):
        route_path = "/" + requested_path
        if request.method == "POST":
            if is_rate_limited(request.remote_addr or "unknown"):
                message = "Too many submissions. Please try again in a minute."
                wants_json = request.is_json or "application/json" in request.headers.get("Accept", "")
                if wants_json or route_path.startswith("/api/"):
                    return jsonify(ok=False, success=False, message=message), 429
                return Response(message, status=429, mimetype="text/plain")
            saved, message = save_submission(route_path)
            wants_json = request.is_json or "application/json" in request.headers.get("Accept", "")
            if not saved:
                if wants_json or route_path.startswith("/api/"):
                    return jsonify(ok=False, success=False, message=message), 422
                return Response(message, status=422, mimetype="text/plain")
            if wants_json or route_path.startswith("/api/"):
                return jsonify(ok=True, success=True, message=message)
            return redirect("/?submitted=1", code=303)

        public_dir = Path(app.config["PUBLIC_DIR"])
        candidate = (public_dir / requested_path).resolve()
        try:
            candidate.relative_to(public_dir.resolve())
        except ValueError:
            candidate = public_dir / "__blocked__"
        if requested_path and candidate.is_file():
            return send_from_directory(public_dir, requested_path)
        return page_response(route_path)

    @app.after_request
    def production_headers(response: Response):
        response.headers["X-EFL-Runtime"] = "Flask"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'",
        )
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if response.mimetype == "text/html":
            if request.method in ("GET", "HEAD"):
                response.headers["Cache-Control"] = "public, max-age=300, must-revalidate"
            else:
                response.headers["Cache-Control"] = "no-store"
        elif response.mimetype not in ("application/json",):
            response.headers.setdefault("Cache-Control", "public, max-age=86400")
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
