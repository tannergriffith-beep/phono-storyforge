# eval/ — Phase 3 closed-loop simulation harness.
#
# Deterministic, non-LLM machinery used to close and measure the tutor loop:
#   - book_builder.py:      assembles decodable practice text for an Objective.
#   - simulated_learner.py: a latent-mastery "child" that reads a book aloud.
#   - loop.py:              wires objective -> book -> read -> miscue -> mastery.
#   - experiments/:         the adaptive-vs-static evidence experiment (the GATE).
#
# Nothing here calls the LLM agent in app/agent.py — the experiment must be fast
# and reproducible. The LLM agent stays the production/demo path.
