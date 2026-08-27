from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, redirect, request, send_from_directory

APP_ROOT = Path(__file__).resolve().parent


def normalise_path(value: str) -> str:
    path = "/" + value.lstrip("/")
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder="assets", static_url_path="/assets")
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "efl-by-level"),
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
    except (OSError, json.JSONDecodeError):
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
        except OSError:
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
                    "consent": safe_values.get("marketing_consent", "")[:40],
                    "payload": json.dumps(safe_values, ensure_ascii=False, sort_keys=True),
                }
            )
        return True, "Thank you. Your details have been received."

    @app.get("/health")
    def health():
        return jsonify(status="ok", runtime="flask", pages=len(manifest), application="EFL by Level")

    @app.route("/", methods=["GET", "HEAD", "POST"])
    @app.route("/<path:requested_path>", methods=["GET", "HEAD", "POST"])
    def dispatch(requested_path: str = ""):
        route_path = "/" + requested_path
        if request.method == "POST":
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
        if response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
