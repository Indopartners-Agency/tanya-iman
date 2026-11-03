"""Text measurement shared by the runtime validator and the admin editor.

There is exactly one word-counting function in this project, and this is it.
The admin editor's live counter (Admin UX section 10) imports the same rule via
``web/shared``. If the editor says 249 and the backend says 251, the editor
stops trusting the tool and live validation becomes worse than useless.

Any change here must be mirrored in web/shared/src/word-count.ts, and
tests/test_text.py plus web/shared's test cover the same edge cases.
"""

from __future__ import annotations

import re

# A "word" is a run of characters containing at least one letter or digit.
# Standalone punctuation ("—", "•") does not count; hyphenated and apostrophised
# forms count once ("anak-anak", "Al-Masih").
_WORD = re.compile(r"[^\W_]+(?:[-'\u2019][^\W_]+)*", re.UNICODE)

MIN_WORDS = 25
MAX_WORDS = 350


def count_words(text: str) -> int:
    """Count words in an Indonesian answer body.

    Counts the answer text only. Citations and rendered scripture labels are
    added by the response assembler and are excluded from F-11 by definition.
    """
    return len(_WORD.findall(text or ""))


def within_length_bounds(text: str) -> bool:
    """F-11: 25 <= words <= 350."""
    return MIN_WORDS <= count_words(text) <= MAX_WORDS
