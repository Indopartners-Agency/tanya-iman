"""Config integrity.

These tests are cheap and they catch the class of mistake that is otherwise
found in production: a typo'd domain, a missing response key, a prompt file that
was renamed.
"""

import pytest

from config import approved_domains, approved_sites, prompt, response, responses, topic_slugs
from config.loader import crisis_config

REQUIRED_RESPONSE_KEYS = {
    "greeting",
    "source_note",
    "refusal",
    "no_grounding",
    "fallback",
    "rate_limit",
    "error",
    "identity",
    "input_too_long",
    "input_empty",
}


def test_exactly_five_approved_sites():
    """PRD F-41 / §6.8. Version 1.0 starts with five. When a sixth site is
    added, update this count, the PRD, and the citation allowlist together."""
    assert len(approved_sites()["sites"]) == 5


def test_approved_domains_are_bare_hostnames():
    for domain in approved_domains():
        assert not domain.startswith("http")
        assert "/" not in domain


def test_all_required_response_keys_exist():
    assert set(responses()) >= REQUIRED_RESPONSE_KEYS


def test_rate_limit_response_interpolates_minutes():
    text = response("rate_limit", minutes=12)
    assert "12" in text
    assert "{" not in text


@pytest.mark.parametrize("name", ["classifier", "composer", "repair", "judge"])
def test_prompt_files_load_without_comment_lines(name):
    text = prompt(name)
    assert text
    assert not any(line.startswith("#") for line in text.splitlines())


def test_topic_taxonomy_has_a_fallback_bucket():
    """Every question gets a topic. Without `lainnya`, the classifier is forced
    to mislabel the ones that fit nowhere, which poisons admin analytics."""
    assert "lainnya" in topic_slugs()


def test_crisis_script_is_still_unapproved():
    """This test is expected to fail the day the editorial team signs off, and
    that failure is the reminder to remove it. Until then it documents that
    what is in the repo is a placeholder."""
    assert crisis_config()["approved"] is False, (
        "Crisis script is now approved — delete this test, confirm verified_on "
        "is set, and re-read PIP B1 before shipping."
    )
