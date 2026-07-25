from __future__ import annotations

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

        health = client.get("/health")
        assert health.status_code == 200
        document = health.get_json()
        assert document["runtime"] == "flask"
        assert document["pages"] >= 10

        submission = client.post(
            "/api/leads",
            json={"email": "test@example.com", "consent": "yes"},
            headers={"Accept": "application/json"},
        )
        assert submission.status_code == 200
        assert submission.get_json()["success"] is True
        assert submissions.exists()

        print(json.dumps({"status": "ok", "runtime": "flask", "pages": document["pages"]}, sort_keys=True))


if __name__ == "__main__":
    main()
