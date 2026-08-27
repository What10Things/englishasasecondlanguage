from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from app import create_app


def require_text(client, path: str, *phrases: str) -> None:
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code)
    html = response.get_data(as_text=True)
    missing = [phrase for phrase in phrases if phrase not in html]
    assert not missing, (path, missing)
    assert response.headers.get("X-EFL-Runtime") == "Flask"


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        submissions = Path(directory) / "submissions.csv"
        app = create_app({"TESTING": True, "SUBMISSIONS_PATH": str(submissions)})
        client = app.test_client()

        require_text(client, "/", "English that meets you", "Two clear journeys")
        require_text(client, "/english-level-test/", "24 short questions", "Find your starting point")
        require_text(client, "/learn-english/a1/", "Core grammar")
        require_text(client, "/teach-english/", "Ready-made resources", "Teacher hub")
        require_text(
            client,
            "/privacy-policy/",
            "EnglishAsAForeignLanguage.com is operated by Urban Sky Web Ltd.",
            "17421062",
            "14/2E Docklands Business Centre",
            "Purposes and lawful bases",
            "object to processing based on legitimate interests",
            "Information Commissioner's Office",
            "automatically removed after 24 months",
        )
        require_text(
            client,
            "/terms/",
            "Website operator",
            "Urban Sky Web Ltd",
            "registered in England and Wales",
        )

        health = client.get("/health")
        assert health.status_code == 200
        document = health.get_json()
        assert document["runtime"] == "flask"
        assert document["pages"] >= 10

        submission = client.post(
            "/api/leads",
            json={"name": "Test", "email": "test@example.com", "privacy_ack": "yes", "unexpected": "discard me"},
            headers={"Accept": "application/json"},
        )
        assert submission.status_code == 200
        assert submission.get_json()["success"] is True
        assert submissions.exists()
        with submissions.open(newline="", encoding="utf-8") as handle:
            row = next(csv.DictReader(handle))
        payload = json.loads(row["payload"])
        assert "unexpected" not in payload
        assert payload["privacy_ack"] == "yes"

        rejected = client.post(
            "/api/leads",
            json={"name": "Test", "email": "test@example.com"},
            headers={"Accept": "application/json"},
        )
        assert rejected.status_code == 422

        homepage = client.get("/").get_data(as_text=True)
        assert "Accept analytics" not in homepage
        assert "Cookie settings" not in homepage

        print(json.dumps({"status": "ok", "runtime": "flask", "pages": document["pages"]}, sort_keys=True))


if __name__ == "__main__":
    main()
