from __future__ import annotations

import csv
import json
import re
import tempfile
import time
from pathlib import Path
from xml.etree import ElementTree

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

        require_text(client, "/", "English that meets you", "Take the free level test", "Get the free starter pack")

        homepage_html = client.get("/").get_data(as_text=True)
        ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', homepage_html)
        assert ld_match, "expected a JSON-LD block on the homepage"
        structured_data = json.loads(ld_match.group(1))
        graph_types = {node["@type"] for node in structured_data["@graph"]}
        assert {"WebSite", "Organization"} <= graph_types
        assert '<link rel="canonical" href="https://englishasaforeignlanguage.com/">' in homepage_html

        require_text(client, "/english-level-test/", "24 short questions", "Find your starting point")
        require_text(client, "/learn-english/a1/", "Core grammar")
        require_text(client, "/teach-english/", "Ready-made resources", "Find what your lesson needs")
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

        formula_submission = client.post(
            "/api/leads",
            json={"name": "=cmd", "email": "formula@example.com", "privacy_ack": "yes"},
            headers={"Accept": "application/json"},
        )
        assert formula_submission.status_code == 200
        with submissions.open(newline="", encoding="utf-8") as handle:
            last_row = list(csv.DictReader(handle))[-1]
        assert last_row["name"] == "'=cmd", "CSV formula-injection guard did not sanitise leading '='"

        rate_limit_ip = {"REMOTE_ADDR": "203.0.113.7"}
        for _ in range(10):
            client.post(
                "/api/leads",
                json={"name": "Rate", "email": "rate@example.com", "privacy_ack": "yes"},
                headers={"Accept": "application/json"},
                environ_overrides=rate_limit_ip,
            )
        limited = client.post(
            "/api/leads",
            json={"name": "Rate", "email": "rate@example.com", "privacy_ack": "yes"},
            headers={"Accept": "application/json"},
            environ_overrides=rate_limit_ip,
        )
        assert limited.status_code == 429, "expected rate limiting to trigger after repeated submissions"

        homepage_response = client.get("/")
        assert homepage_response.headers.get("Content-Security-Policy")
        assert homepage_response.headers.get("Strict-Transport-Security")
        assert "max-age=300" in homepage_response.headers.get("Cache-Control", "")

        homepage = homepage_response.get_data(as_text=True)
        assert "Accept analytics" not in homepage
        assert "Cookie settings" not in homepage

        # Same-origin POST (Origin header matching Host) must succeed.
        same_origin = client.post(
            "/api/leads",
            json={"name": "Origin Test", "email": "origin@example.com", "privacy_ack": "yes"},
            headers={"Accept": "application/json", "Origin": "http://localhost"},
        )
        assert same_origin.status_code == 200, "same-origin POST with matching Origin should succeed"

        # Cross-site POST (Origin header mismatching Host) must be rejected.
        cross_site = client.post(
            "/api/leads",
            json={"name": "Cross Site", "email": "cross@example.com", "privacy_ack": "yes"},
            headers={"Accept": "application/json", "Origin": "https://evil.example"},
        )
        assert cross_site.status_code == 403, "cross-site POST with mismatched Origin should be rejected"
        assert cross_site.get_json()["success"] is False

        # Sec-Fetch-Site is authoritative when present, even without a matching Origin.
        cross_site_fetch_metadata = client.post(
            "/api/leads",
            json={"name": "Cross Fetch", "email": "crossfetch@example.com", "privacy_ack": "yes"},
            headers={"Accept": "application/json", "Sec-Fetch-Site": "cross-site"},
        )
        assert cross_site_fetch_metadata.status_code == 403

        same_site_fetch_metadata = client.post(
            "/api/leads",
            json={"name": "Same Fetch", "email": "samefetch@example.com", "privacy_ack": "yes"},
            headers={"Accept": "application/json", "Sec-Fetch-Site": "same-origin"},
        )
        assert same_site_fetch_metadata.status_code == 200

        # No-JS/very old clients sending neither header must still be able to submit.
        no_headers = client.post(
            "/api/leads",
            json={"name": "No Headers", "email": "noheaders@example.com", "privacy_ack": "yes"},
        )
        assert no_headers.status_code == 200

        # No-JS level-test fallback: self-assessment guide present, no scoring claim.
        require_text(
            client,
            "/english-level-test/",
            "test-noscript",
            "This is a guide, not an automated score.",
        )

        sitemap_response = client.get("/sitemap.xml")
        assert sitemap_response.status_code == 200
        sitemap_xml = ElementTree.fromstring(sitemap_response.get_data(as_text=True))
        locs = [element.text for element in sitemap_xml.iter() if element.tag.endswith("loc")]
        assert len(locs) >= 40, f"expected the full crawled route set in sitemap.xml, got {len(locs)}"
        assert all(loc.startswith("https://englishasaforeignlanguage.com/") for loc in locs)
        assert not any(loc.endswith("/404/") for loc in locs), "404 page must not be indexed"
        assert f"https://englishasaforeignlanguage.com/learn-english/grammar/" in locs

        # Daily retention maintenance runs opportunistically on GET traffic
        # without a GoDaddy cron job, independent of new submissions.
        marker = submissions.parent / ".last_retention_prune"
        client.get("/")
        assert marker.exists(), "GET traffic should trigger the daily maintenance marker"
        first_run = marker.stat().st_mtime
        client.get("/")
        assert marker.stat().st_mtime == first_run, "maintenance should not re-run within the same day"
        old_time = time.time() - 90000
        import os

        os.utime(marker, (old_time, old_time))
        client.get("/")
        assert marker.stat().st_mtime > old_time, "maintenance should re-run once the marker is more than 24h old"

        print(json.dumps({"status": "ok", "runtime": "flask", "pages": document["pages"]}, sort_keys=True))


if __name__ == "__main__":
    main()
