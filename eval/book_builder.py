# eval/book_builder.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — deterministic book builder (Phase 3).
#
# This is the EXPERIMENT's book source. Given an Objective from the planner, it
# assembles short decodable practice text that (a) exercises the target
# grapheme, (b) folds in the spaced-review graphemes, and (c) stays inside the
# learner's mastered-level budget so every word is decodable.
#
# Why not app/agent.py (the LLM writer)? The N-session experiment needs to run
# fast, offline, and identically every time. An LLM call is slow, rate-limited,
# and non-deterministic, which would make the result chart unreproducible. So
# the experiment uses THIS deterministic builder; the LLM agent remains the
# production/demo path. Same through-line either way: the deterministic
# decodability engine (decompose) is the source of truth for what's allowed.
# =============================================================================

from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.phonics_db import GRAPHEME_INVENTORY, GRAPHEME_LEVEL, LEVEL_SEQUENCE
from app.schemas import Objective
from app.skills.decodability import (
    decompose,
    inflectional_suffix,
    is_word_decodable,
)

# A pool of single-syllable decodable words spanning the phonics scope-and-
# sequence. Indexed by the graphemes each word exercises so the builder can pull
# words that target any given grapheme. Curated (not LLM-generated) to keep the
# experiment deterministic and offline.
_CORPUS_TEXT = """
cat hat map bat rat sat fat mat pad sad mad bad dad had bag tag rag wag nag jam ham yam ram
can man pan ran fan tan tap lap nap cap gap wax tax cab nab lab dab gas
bed red led fed wed beg leg peg hen pen ten den men net pet vet jet wet get let met set web egg
big pig dig fig wig win pin fin tin bin sit fit hit kit lit pit bit dim rim him fix mix six
hot pot dot got lot not cot top mop hop cop pop log dog fog jog box fox cob job rob sob nod rod cod
sun run bun fun gun nun cup pup cut gut hut nut but bug rug mug jug hug tug tub cub rub mud bud
zip zap zig zag buzz fizz fuzz jazz zigzag
shop ship shed shot fish dish wish cash dash rash gash mash hush rush shut
chip chop chin chat chum chug chap rich much such
thin this that then them thud bath path math with moth
whip whiz when whim
duck sock rock lock kick pick sick lick neck deck peck back pack sack tack rack
quit quiz
stop step spin spit spot snap slap clap clip flap flag flat plan plot plug glad grab grin trap trip
drum drop frog from crab crib club blob slim swim twin twig
fast last list must dust nest test best rest milk silk help yelp belt melt felt jump bump lump
hand land sand band bend send lend pond fond hint mint tent rent went sent lift gift sift soft
cake bake lake make take wake game name same came fame lane cane mane plane grape
bike like hike bite kite mile pile time lime dime fine line mine nine vine wide ride side hide
hope rope note rose nose home bone cone stone slope
cube tube cute mute use rule mule eve theme these
car bar far jar tar star scar hard card yard farm harm arm art cart part dart
her herd fern term
bird girl
for fork corn born torn cord sort port short storm
fur turn burn hurt curl surf
rain main pain wait paid tail nail sail mail jail rail snail train
day say way play stay clay tray gray
see bee tree free feet meet seed need deed week keep deep sleep green
eat seat meat beat heat read leaf team bean mean clean dream
boat coat road soap goat load toad
toe doe
pie tie die lie
high night light right sight might fight tight bright
moon soon zoo food mood room boot root tooth
out loud cloud mouth round found sound ground proud
cow now how down town brown crown clown
boil coil soil oil join coin point
boy toy joy
saw paw jaw law claw draw straw
haul fault haunt vault
all ball call fall hall mall tall wall small
bank tank rank sank thank drank blank
pink link sink wink think drink blink
king sing ring wing thing bring sting swing
song long gong strong
hung rung lung sung stung
honk bonk conk
junk sunk bunk trunk skunk
bang rang sang hang gang fang
my by fly try sky shy spy cry dry sly fry
happy puppy funny sunny bunny silly jelly belly penny daddy muddy
cats dogs pigs hats maps bugs cups beds pens
boxes foxes dishes wishes
jumped helped landed wanted napped
jumping helping running sitting reading
"""

# Light decodable/sight connectors so a page reads like text rather than a word
# list. They are sight words for the learner (no grapheme evidence attributed).
_CONNECTORS = ["the", "a", "and", "is", "can", "on", "in", "it"]


def _build_corpus() -> list[str]:
    seen: set[str] = set()
    words: list[str] = []
    for w in _CORPUS_TEXT.split():
        d = decompose(w, mastered_levels=LEVEL_SEQUENCE)
        if d.is_decodable and d.word not in seen:
            seen.add(d.word)
            words.append(d.word)
    return words


CORPUS: list[str] = _build_corpus()


def _grapheme_keys(word: str) -> set[str]:
    """All inventory keys a word exercises, including the structural sentinels."""
    d = decompose(word, mastered_levels=LEVEL_SEQUENCE)
    keys = {g.grapheme for g in d.graphemes}
    gs = d.graphemes
    if any(gs[i].kind == "C" and gs[i + 1].kind == "C" for i in range(len(gs) - 1)):
        keys.add("_blend_")
    suffix = inflectional_suffix(d.word)
    if suffix:
        keys.add(f"-{suffix}")
    return keys


# grapheme key -> sorted words exercising it (deterministic order).
_INDEX: dict[str, list[str]] = {}
for _w in CORPUS:
    for _k in _grapheme_keys(_w):
        _INDEX.setdefault(_k, []).append(_w)
for _k in _INDEX:
    _INDEX[_k] = sorted(set(_INDEX[_k]))


def _level_budget(level: str) -> list[str]:
    """The mastered-level budget assumed when a grapheme is the frontier target:
    every level up to and including its own, in curriculum order."""
    return LEVEL_SEQUENCE[: LEVEL_SEQUENCE.index(level) + 1]


def _compute_unteachable() -> frozenset[str]:
    """Graphemes with no decodable single-syllable word at their introduction budget.

    With this corpus that is exactly the 'ng' and 'ph' digraphs: 'ng' only occurs
    in glued rimes or in clusters that trip the blend rule, and 'ph' has no
    short-vowel-only word. Such graphemes are excluded from the simulated
    curriculum (the loop pre-masters them) so the planner never stalls on a
    target it can never get evidence for.
    """
    unteachable: set[str] = set()
    for grapheme, level in GRAPHEME_INVENTORY:
        budget = _level_budget(level)
        words = _INDEX.get(grapheme, [])
        if not any(is_word_decodable(w, budget) for w in words):
            unteachable.add(grapheme)
    return frozenset(unteachable)


UNTEACHABLE_GRAPHEMES: frozenset[str] = _compute_unteachable()


def target_words(objective: Objective) -> list[str]:
    """Corpus words that exercise the objective's target grapheme and are
    decodable within the objective's budget (mastered levels + the target level)."""
    budget = list(objective.mastered_levels)
    if objective.target_level not in budget:
        budget.append(objective.target_level)
    return [
        w
        for w in _INDEX.get(objective.target_grapheme, [])
        if is_word_decodable(w, budget)
    ]


def _decodable_filler(budget: list[str]) -> list[str]:
    """All corpus words decodable within a budget (deterministic order)."""
    return [w for w in CORPUS if is_word_decodable(w, budget)]


@dataclass
class Book:
    """A short decodable practice passage targeting one Objective."""

    title: str
    words: list[str]
    target_grapheme: str
    objective: Objective
    sight_words: set[str] = field(default_factory=set)

    @property
    def text(self) -> str:
        return " ".join(self.words)


def build_book(
    objective: Objective,
    *,
    session_index: int = 0,
    num_target: int = 6,
    length: int = 16,
    sight_words: set[str] | None = None,
    rng: random.Random | None = None,
) -> Book:
    """Builds a decodable practice book for an objective.

    The passage is composed of: several words exercising the target grapheme,
    one word per spaced-review grapheme, decodable filler to reach `length`, and
    a few sight-word connectors so it reads like text. Selection is deterministic
    given the inputs (an optional seeded rng only varies which words are drawn,
    never decodability), so the experiment reproduces exactly.
    """
    budget = list(objective.mastered_levels)
    if objective.target_level not in budget:
        budget.append(objective.target_level)

    sight = set(sight_words or set()) | set(_CONNECTORS)

    def _rotate(words: list[str], n: int) -> list[str]:
        """Deterministically pick n words, rotating by session for variety."""
        if not words:
            return []
        if rng is not None:
            pool = list(words)
            rng.shuffle(pool)
            chosen = pool[:n]
        else:
            offset = session_index % len(words)
            chosen = [words[(offset + i) % len(words)] for i in range(n)]
        return chosen

    targets = target_words(objective)
    chosen_targets = _rotate(targets, num_target) if targets else []

    review: list[str] = []
    for g in objective.review_graphemes:
        cands = [w for w in _INDEX.get(g, []) if is_word_decodable(w, budget)]
        if cands:
            review.append(_rotate(cands, 1)[0])

    body = chosen_targets + review
    if len(body) < length:
        filler_pool = [w for w in _decodable_filler(budget) if w not in set(body)]
        body += _rotate(filler_pool, length - len(body))

    # Interleave a connector every few content words for readability.
    words: list[str] = []
    for i, w in enumerate(body):
        if i > 0 and i % 4 == 0:
            words.append(_CONNECTORS[(i // 4) % len(_CONNECTORS)])
        words.append(w)

    title = f"The {objective.target_grapheme} Book"
    return Book(
        title=title,
        words=words,
        target_grapheme=objective.target_grapheme,
        objective=objective,
        sight_words=sight,
    )
