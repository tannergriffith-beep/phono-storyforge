# app/tutor/ — the closed loop as a product.
#
# This package lifts the closed loop proven in eval/loop.py (objective -> book
# -> read -> miscue analysis -> BKT update -> persist) out of the simulation and
# into a real, stateful tutor that runs against a persistent LearnerStore. Stage
# A swaps only the two simulated nodes for real ones:
#   - the simulated reader -> a real read-aloud transcript (typed for now;
#     Gemini Live voice in Stage B),
#   - and keeps the deterministic book builder as the Stage-A content source
#     (the verifier-gated LLM generator replaces it in Stage B).
# Everything load-bearing (planner, alignment, BKT mastery, store) is reused
# unchanged.
from app.tutor.session import PreparedSession, SessionOutcome, TutorSession

__all__ = ["TutorSession", "PreparedSession", "SessionOutcome"]
