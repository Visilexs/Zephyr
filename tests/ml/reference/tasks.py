"""M1b synthetic tasks, standard library only; generator version 1.

Input ends at ANSWER: the supervised answer is never appended. The answer's
value necessarily occurs in A's assignments and B's original candidates.
Composition holds out declared *pairs*, not individual vocabulary tokens.
"""

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import random
from types import MappingProxyType


GENERATOR_VERSION = 1
KEYS = tuple(f'k{i}' for i in range(16))
VALUES = tuple(f'v{i}' for i in range(8))
NOISE = tuple(f'n{i}' for i in range(16))
CANDIDATES = tuple(f'c{i}' for i in range(8))
DELIMITERS = ('SET', 'NOISE', 'QUERY', 'ANSWER', 'PAD', 'THINK')
CLUES = MappingProxyType({
    f'S{mask:02x}': frozenset(CANDIDATES[i] for i in range(8) if mask & (1 << i))
    for mask in range(256) if mask.bit_count() >= 2
})
NEUTRAL = 'Sff'
VOCABULARY_A = frozenset(KEYS + VALUES + NOISE + DELIMITERS)
VOCABULARY_B = frozenset(CANDIDATES + tuple(CLUES) + DELIMITERS)
HELD_OUT_A = frozenset(
    frozenset(((KEYS[i], value), (KEYS[i + 1], value)))
    for i in range(0, 16, 2) for value in VALUES
)
HELD_OUT_B = frozenset(
    (left, right) for left in CLUES for right in CLUES
    if left != right and len(CLUES[left]) == len(CLUES[right]) < 8
)


@dataclass(frozen=True)
class Example:
    tokens: tuple[str, ...]
    target: str


def token_hash(tokens):
    """Hash only canonical input tokens, never labels or split metadata."""
    return sha256('\n'.join(tokens).encode('ascii')).hexdigest()


def parse_a(tokens):
    """Validate A's grammar and recover assignments and query from input only."""
    assignments = {}
    i = 0
    while i < len(tokens) and tokens[i] == 'SET':
        if i + 2 >= len(tokens):
            raise ValueError('Truncated assignment')
        key, value = tokens[i + 1:i + 3]
        if key not in KEYS or value not in VALUES or key in assignments:
            raise ValueError('Invalid or repeated assignment')
        assignments[key] = value
        i += 3
    if not assignments or i >= len(tokens) or tokens[i] != 'NOISE':
        raise ValueError('Missing assignments or NOISE')
    i += 1
    while i < len(tokens) and tokens[i] in NOISE:
        i += 1
    if (len(tokens) - i != 3 or tokens[i] != 'QUERY'
            or tokens[i + 1] not in KEYS or tokens[i + 2] != 'ANSWER'):
        raise ValueError('Invalid query suffix')
    return assignments, tokens[i + 1]


def solve_a(tokens):
    """Return a dict-lookup answer, or None for an unassigned query."""
    assignments, query = parse_a(tokens)
    return assignments.get(query)


def parse_b(tokens):
    """Read a unique candidate list followed by catalog clues and ANSWER."""
    i = 0
    candidates = set()
    while i < len(tokens) and tokens[i] in CANDIDATES:
        if tokens[i] in candidates:
            raise ValueError('Repeated candidate')
        candidates.add(tokens[i])
        i += 1
    if not candidates or not tokens or tokens[-1] != 'ANSWER':
        raise ValueError('Missing candidates or ANSWER')
    clues = tokens[i:-1]
    if not clues or any(clue not in CLUES for clue in clues):
        raise ValueError('Invalid clue sequence')
    return candidates, clues


def solve_b(tokens):
    """Return the unique intersection member; None means ambiguous/inconsistent."""
    feasible, clues = parse_b(tokens)
    for clue in clues:
        feasible.intersection_update(CLUES[clue])
    return next(iter(feasible)) if len(feasible) == 1 else None


def generate_a(rng, n, d):
    """Sample IID values, unique keys, random assignment order and uniform query."""
    if not 2 <= n <= len(KEYS) or d < 0:
        raise ValueError('Invalid A difficulty')
    keys = rng.sample(KEYS, n)
    assignments = [(key, rng.choice(VALUES)) for key in keys]
    query = rng.choice(keys)
    rng.shuffle(assignments)
    tokens = tuple(token for key, value in assignments for token in ('SET', key, value))
    tokens += ('NOISE',) + tuple(rng.choices(NOISE, k=d)) + ('QUERY', query, 'ANSWER')
    return Example(tokens, dict(assignments)[query])


def generate_b(rng, informative, delay, target=None):
    """Strictly shrink ambiguity, then resolve with an independently ambiguous clue."""
    if not 2 <= informative <= 4 or delay < 0 or target not in (None, *CANDIDATES):
        raise ValueError('Invalid B difficulty or target')
    target = rng.choice(CANDIDATES) if target is None else target
    candidates = rng.sample(CANDIDATES, len(CANDIDATES))
    feasible = set(candidates)
    clues = []
    for index in range(informative - 1):
        # Leave enough candidates for every remaining clue to be informative.
        choices = [clue for clue, subset in CLUES.items()
                   if target in subset
                   and informative - index <= len(feasible & subset) < len(feasible)]
        clue = rng.choice(choices)
        clues.append(clue)
        feasible.intersection_update(CLUES[clue])
    excluded = set(candidates) - feasible
    choices = [clue for clue, subset in CLUES.items()
               if feasible & subset == {target} and excluded & subset]
    final = rng.choice(choices)
    # Full-universe clues are neutral at every position, including before clue 1.
    for _ in range(delay):
        clues.insert(rng.randrange(len(clues) + 1), NEUTRAL)
    tokens = tuple(candidates + clues + [final, 'ANSWER'])
    example = Example(tokens, target)
    if solve_b(tokens) != target or len(set(candidates) & CLUES[final]) < 2:
        raise ValueError('Construction failed uniqueness/late-clue constraints')
    return example


def is_compositional(task, tokens):
    """A reserves same-value adjacent-key pairs; B reserves equal-size clue pairs."""
    if task == 'A':
        assignments, _ = parse_a(tokens)
        return any(frozenset(pair) in HELD_OUT_A for pair in combinations(assignments.items(), 2))
    if task == 'B':
        _, clues = parse_b(tokens)
        informative = [clue for clue in clues if clue != NEUTRAL]
        return len(informative) >= 2 and tuple(informative[:2]) in HELD_OUT_B
    raise ValueError('Unknown task')


def make_splits(task, seed=1729, train_size=4096, split_size=2048):
    """Create balanced, shuffled, globally deduplicated deterministic manifests.

    Counts must be multiples of eight. Each batch shares difficulty across all
    labels, giving identical length distributions without exposing batch metadata.
    Train/validation exclude reserved combinations; composition requires them;
    length excludes them to isolate length extrapolation. A length tests extend
    n only, d only, or both. B length tests extend neutral delay to 64..128.
    """
    if task not in ('A', 'B') or any(size <= 0 or size % 8 for size in (train_size, split_size)):
        raise ValueError('Unknown task or sizes not positive multiples of eight')
    rng = random.Random(seed)
    labels = VALUES if task == 'A' else CANDIDATES
    seen = set()
    splits = {}
    for name in ('train', 'validation', 'composition', 'length'):
        examples = []
        size = train_size if name == 'train' else split_size
        for _ in range(size // 8):
            n, d = rng.randint(2, 8), rng.randint(0, 32)
            informative = rng.randint(2, 4)
            if name == 'length':
                extension = rng.randrange(3)
                if task == 'A' and extension != 1:
                    n = rng.randint(9, 16)
                if task == 'B' or extension != 0:
                    d = rng.randint(64, 128)
            for target in labels:
                for attempt in range(100000):
                    example = (generate_a(rng, n, d) if task == 'A'
                               else generate_b(rng, informative, d, target))
                    if example.target != target:
                        continue
                    if is_compositional(task, example.tokens) != (name == 'composition'):
                        continue
                    digest = token_hash(example.tokens)
                    if digest not in seen:
                        seen.add(digest)
                        examples.append(example)
                        break
                else:
                    raise RuntimeError('Rejection budget exhausted')
        rng.shuffle(examples)
        splits[name] = tuple(examples)
    hashes = [{token_hash(example.tokens) for example in split} for split in splits.values()]
    assert all(left.isdisjoint(right) for left, right in combinations(hashes, 2))
    return splits


def ambiguous_b(rng):
    """Rejection-sample an unlabeled input whose intersection stays ambiguous."""
    catalog = tuple(CLUES)
    for _ in range(10000):
        candidates = tuple(rng.sample(CANDIDATES, 8))
        clues = tuple(rng.choices(catalog, k=rng.randint(2, 4)))
        feasible = set(candidates)
        for clue in clues:
            feasible.intersection_update(CLUES[clue])
        if len(feasible) >= 2:
            return candidates + clues + ('ANSWER',)
    raise RuntimeError('Ambiguous rejection budget exhausted')
