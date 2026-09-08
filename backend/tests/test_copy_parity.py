"""Copy parity between backend and client.

The greeting the seeker reads on first load is rendered by the client; the same
greeting is what the backend considers canonical. Two copies of a string that
must match is a defect waiting to happen, so this test asserts they do.

Multi-paragraph strings (refusal, no_grounding, fallback) live only in the
backend — the client renders them from `answer_text` — so they are not compared.
"""

import json
from pathlib import Path

from config import responses

LOCALE_PATH = Path(__file__).resolve().parents[2] / "web" / "app" / "locales" / "id.json"


def test_shared_copy_is_byte_identical():
    locale = json.loads(LOCALE_PATH.read_text(encoding="utf-8"))
    backend = responses()

    mismatches = {
        key: (value, backend.get(key))
        for key, value in locale["shared"].items()
        if backend.get(key) != value
    }

    assert not mismatches, (
        "Client and backend copy have drifted. Update both, and record the "
        f"editorial sign-off in the PR: {mismatches}"
    )
