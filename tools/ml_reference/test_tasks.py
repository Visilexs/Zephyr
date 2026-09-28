"""Run with python tools/ml_reference/test_tasks.py; no third-party dependencies."""

from collections import Counter, defaultdict
from itertools import combinations
import random

from tasks import (
    CANDIDATES, CLUES, KEYS, NEUTRAL, NOISE, VALUES, VOCABULARY_A, VOCABULARY_B,
    ambiguous_b, generate_a, is_compositional, make_splits, parse_a, parse_b,
    solve_a, solve_b, token_hash,
)


def main():
    """Check A30/A31, including independent reconstruction and anti-shortcut gates."""
    checks = 0

    def passed(message):
        nonlocal checks
        checks += 1
        print(f'PASS: {message}')

    for task in ('A', 'B'):
        splits = make_splits(task)
        repeated = make_splits(task)
        hashes = {}
        for name, examples in splits.items():
            ordered = tuple(token_hash(example.tokens) for example in examples)
            assert ordered == tuple(token_hash(example.tokens) for example in repeated[name])
            assert examples == repeated[name]
            assert len(set(ordered)) == len(examples)
            hashes[name] = set(ordered)
        assert all(left.isdisjoint(right) for left, right in combinations(hashes.values(), 2))
        changed = make_splits(task, seed=1730, train_size=8, split_size=8)
        assert changed['train'] != splits['train'][:8]
        passed(f'A31 Task {task}: seeded hashes reproducible, unique and pairwise disjoint')

        vocabulary = VOCABULARY_A if task == 'A' else VOCABULARY_B
        labels = VALUES if task == 'A' else CANDIDATES
        solver = solve_a if task == 'A' else solve_b
        observed_train = set(token for example in splits['train'] for token in example.tokens)
        assert isinstance(vocabulary, frozenset)
        count = 0
        length_bins = set()
        for name, examples in splits.items():
            counts = Counter(example.target for example in examples)
            lengths = defaultdict(list)
            for example in examples:
                tokens = example.tokens
                assert set(tokens) <= vocabulary
                if name != 'train':
                    assert set(tokens) <= observed_train
                assert solver(tokens) == example.target
                # The spec forbids an appended answer, not its occurrence in evidence.
                assert tokens[-1] == 'ANSWER' and tokens.count('ANSWER') == 1
                assert tokens[tokens.index('ANSWER') + 1:] == ()
                assert is_compositional(task, tokens) == (name == 'composition')
                lengths[example.target].append(len(tokens))
                if task == 'A':
                    assignments, query = parse_a(tokens)
                    assert query in assignments and len(assignments) == tokens.count('SET')
                    n = len(assignments)
                    d = sum(token in NOISE for token in tokens)
                    assert not (set(NOISE) & (set(KEYS) | set(VALUES)))
                    if name == 'length':
                        assert 9 <= n <= 16 or 64 <= d <= 128
                        length_bins.add((n > 8, d > 32))
                    else:
                        assert 2 <= n <= 8 and 0 <= d <= 32
                else:
                    original, clues = parse_b(tokens)
                    assert original == set(CANDIDATES)
                    feasible = original.copy()
                    informative = 0
                    for index, clue in enumerate(clues):
                        previous = feasible.copy()
                        feasible.intersection_update(CLUES[clue])
                        if clue != NEUTRAL:
                            assert feasible < previous
                            informative += 1
                        assert len(feasible) == 1 if index == len(clues) - 1 else len(feasible) >= 2
                    assert 2 <= informative <= 4
                    assert len(original & CLUES[clues[-1]]) >= 2
                    assert feasible == {example.target}
                    d = clues.count(NEUTRAL)
                    assert 64 <= d <= 128 if name == 'length' else 0 <= d <= 32
                count += 1
            assert set(counts) == set(labels)
            assert max(counts.values()) - min(counts.values()) == 0
            means = [sum(lengths[label]) / len(lengths[label]) for label in labels]
            assert max(means) - min(means) <= 1e-12
            # Stronger than matching means: full empirical length histograms match.
            assert all(Counter(lengths[label]) == Counter(lengths[labels[0]]) for label in labels)
        assert count >= 2000
        assert splits['composition'] and splits['length']
        if task == 'A':
            assert length_bins == {(True, False), (False, True), (True, True)}
        passed(f'A30 Task {task}: solver agrees on {count} labels; per-example constraints hold')
        passed(f'A31 Task {task}: frozen/observed train vocabulary covers tests; composition/length bins verified')
        passed(f'Task {task}: exact class balance (tolerance 0); class mean lengths within 1e-12')
        passed(f'A31 Task {task}: input ends at ANSWER with no appended target (spec interpretation)')

        if task == 'A':
            by_query = defaultdict(Counter)
            for example in splits['train']:
                by_query[parse_a(example.tokens)[1]][example.target] += 1
            predictions = {key: max(VALUES, key=lambda value: counts[value])
                           for key, counts in by_query.items()}
            for name in ('validation', 'composition', 'length'):
                examples = splits[name]
                accuracy = sum(predictions[parse_a(example.tokens)[1]] == example.target
                               for example in examples) / len(examples)
                assert abs(accuracy - 1 / len(VALUES)) <= 0.04, (name, accuracy)
            passed('A30 Task A: fitted query-only baseline within chance 0.125 +/- 0.04 on every test split')

    rng = random.Random(93)
    for _ in range(200):
        tokens = ambiguous_b(rng)
        assert solve_b(tokens) is None
        original, clues = parse_b(tokens)
        for clue in clues:
            original.intersection_update(CLUES[clue])
        assert len(original) >= 2
        example = generate_a(rng, 2, 0)
        missing = next(key for key in KEYS if key not in parse_a(example.tokens)[0])
        assert solve_a(example.tokens[:-2] + (missing, 'ANSWER')) is None
    passed('A30: 200 unlabeled ambiguous B inputs and unassigned A queries have no unique answer')

    assert solve_a(('SET', 'k2', 'v5', 'SET', 'k7', 'v1', 'NOISE', 'n3',
                    'QUERY', 'k7', 'ANSWER')) == 'v1'
    assert solve_b(('c0', 'c1', 'c2', 'c3', 'S03', 'S06', 'ANSWER')) == 'c1'
    assert solve_b(('c0', 'c1', 'S0c', 'ANSWER')) is None
    invalid = [
        (solve_a, ('SET', 'k0', 'v0', 'SET', 'k0', 'v1', 'NOISE', 'QUERY', 'k0', 'ANSWER')),
        (solve_a, ('SET', 'k0')),
        (solve_a, ('SET', 'k0', 'v0', 'NOISE', 'QUERY', 'k0', 'ANSWER', 'v0')),
        (solve_b, ('c0', 'c0', 'S03', 'ANSWER')),
        (solve_b, ('c0', 'S01', 'ANSWER')),
    ]
    for solver, tokens in invalid:
        try:
            solver(tokens)
        except ValueError:
            continue
        raise AssertionError(('Malformed input accepted', tokens))
    passed('Independent spec fixtures, inconsistent intersections and malformed-input rejection')
    print(f'{checks} check groups passed.')


if __name__ == '__main__':
    main()
