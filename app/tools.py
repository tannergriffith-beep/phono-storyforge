# app/tools.py
#
# Backward-compatibility shim. The decodability engine moved to
# app/skills/decodability.py in Phase 1 of the closed-loop redesign.
# Import from app.skills.decodability in new code; this re-export keeps
# existing imports (and the QA loop) working.

from app.skills.decodability import (  # noqa: F401
    GraphemeHit,
    WordDecomposition,
    check_decodability,
    clean_word,
    decompose,
    is_word_decodable,
)
