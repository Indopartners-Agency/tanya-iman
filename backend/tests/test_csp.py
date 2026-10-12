"""
test_csp.py - Phase 7 Task 7.1

Verifies the `frame-ancestors` Content-Security-Policy header:
  1. With no FRAME_ANCESTORS configured -> 'none' (blocks all framing)
  2. With approved domains set -> lists only those origins
  3. Non-approved origins are NOT present in the policy
"""
import pytest
from fastapi.testclient import TestClient

from config.settings import Settings, get_settings
from main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_with_ancestors(ancestors: str) -> TestClient:
    """Spin up a test client with a specific FRAME_ANCESTORS value."""
    import os

    os.environ["FRAME_ANCESTORS"] = ancestors
    get_settings.cache_clear()
    client = TestClient(app, raise_server_exceptions=True)
    return client


def _csp(client: TestClient) -> str:
    resp = client.get("/health")
    assert resp.status_code == 200
    return resp.headers.get("content-security-policy", "")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCSPFrameAncestors:
    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_no_ancestors_produces_none_policy(self):
        """When FRAME_ANCESTORS is empty, the policy must be 'frame-ancestors 'none''."""
        client = _client_with_ancestors("")
        csp = _csp(client)
        assert "frame-ancestors" in csp
        assert "'none'" in csp

    def test_single_approved_domain_in_policy(self):
        """A single approved origin appears verbatim in the policy."""
        client = _client_with_ancestors("https://isadanislam.org")
        csp = _csp(client)
        assert "frame-ancestors" in csp
        assert "https://isadanislam.org" in csp
        assert "'none'" not in csp

    def test_multiple_approved_domains_all_present(self):
        """All five approved origins are present in the policy."""
        approved = (
            "https://isadanislam.org,"
            "https://isadanalquran.com,"
            "https://isadanalfatihah.com,"
            "https://isaislamdankaumwanita.com,"
            "https://takutneraka.com"
        )
        client = _client_with_ancestors(approved)
        csp = _csp(client)
        for domain in approved.split(","):
            assert domain.strip() in csp, f"Expected {domain.strip()!r} in CSP: {csp!r}"

    def test_unapproved_origin_not_in_policy(self):
        """An arbitrary origin not in the list must not appear in frame-ancestors."""
        client = _client_with_ancestors("https://isadanislam.org")
        csp = _csp(client)
        assert "https://evil.example.com" not in csp

    def test_csp_header_present_on_every_route(self):
        """CSP is set on all routes, not just /health."""
        client = _client_with_ancestors("https://isadanislam.org")
        for path in ["/health", "/api/health"]:
            resp = client.get(path)
            assert "content-security-policy" in resp.headers, (
                f"Missing CSP header on {path}"
            )

    def test_whitespace_trimmed_from_ancestors(self):
        """Spaces around comma-separated domains are stripped correctly."""
        client = _client_with_ancestors("  https://isadanislam.org  ,  https://takutneraka.com  ")
        csp = _csp(client)
        assert "https://isadanislam.org" in csp
        assert "https://takutneraka.com" in csp

    def test_security_headers_also_present(self):
        """X-Content-Type-Options and Referrer-Policy are set alongside CSP."""
        client = _client_with_ancestors("")
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert "strict-origin" in resp.headers.get("referrer-policy", "")
