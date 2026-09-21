"""Freeze the M7 datasets to disk as immutable binary artifacts + a manifest.

Generation logic is tasks.py's and is not modified here: generate_a,
generate_b, is_compositional and token_hash are imported. The only thing this
script changes is the *declared difficulty budget* -- the M7 preset is smaller
than the specification's suggestion, by declaration, and that is recorded in
the manifest. make_splits() in tasks.py hard-codes the spec-sized ranges, so
the split loop is mirrored here with the ranges as constants; everything else
about it (balancing, global deduplication, composition hold-out, length
extension, shuffling, the disjointness assertion) is identical.

Binary format, little-endian:

    magic   : 8 bytes, ASCII "ZML7DATA"
    version : u32 = 1
    n_rows  : u32
    seq_len : u32        (all rows padded to this with the PAD id)
    vocab   : u32        (input vocabulary size)
    n_class : u32        (output vocabulary size, i.e. number of target classes)
    pad_id  : u32
    reserved: u32 = 0
    then n_rows * seq_len  i32 token ids
    then n_rows            i32 targets

The reader is lib/ml/dataset.zeph; both descriptions must stay in step.
"""

import argparse
import json
import os
import random
import struct
import sys
from hashlib import sha256
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import (  # noqa: E402
    CANDIDATES,
    GENERATOR_VERSION,
    VALUES,
    VOCABULARY_A,
    VOCABULARY_B,
    generate_a,
    generate_b,
    is_compositional,
    token_hash,
)

MAGIC = b'ZML7DATA'
FORMAT_VERSION = 1
PRESET = 'm7-reduced'
SEED = 20260921
TRAIN_SIZE = 4096
SPLIT_SIZE = 2048
SPLITS = ('train', 'validation', 'composition', 'length')

# The declared, reduced M7 budget. The specification suggests n=2..8, d=0..32.
A_KEYS = (2, 4)
A_DISTRACTORS = (0, 8)
B_INFORMATIVE = (2, 4)
B_DELAY = A_DISTRACTORS          # B's neutral delay is drawn from the same range
# Length extrapolation is left exactly as tasks.py declares it: the point of
# that split is to test beyond the training range, so it is not reduced.
A_LENGTH_KEYS = (9, 16)
LENGTH_DELAY = (64, 128)

NOTE = (
    'Difficulty is below the specification\'s suggestion by declaration: task A '
    'uses n=2..4 keys and d=0..8 distractors where the spec suggests n=2..8 and '
    'd=0..32. Task B uses 2..4 informative clues with neutral delays drawn from '
    'the same reduced distractor range. The length split keeps tasks.py\'s '
    'unreduced extension ranges, since its purpose is to test beyond training.'
)


def make_splits_reduced(task):
    """tasks.make_splits with the M7 reduced difficulty ranges."""
    rng = random.Random(SEED)
    labels = VALUES if task == 'A' else CANDIDATES
    seen = set()
    splits = {}
    for name in SPLITS:
        examples = []
        size = TRAIN_SIZE if name == 'train' else SPLIT_SIZE
        for _ in range(size // 8):
            n, d = rng.randint(*A_KEYS), rng.randint(*A_DISTRACTORS)
            informative = rng.randint(*B_INFORMATIVE)
            if name == 'length':
                extension = rng.randrange(3)
                if task == 'A' and extension != 1:
                    n = rng.randint(*A_LENGTH_KEYS)
                if task == 'B' or extension != 0:
                    d = rng.randint(*LENGTH_DELAY)
            for target in labels:
                for _attempt in range(100000):
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
    return splits


def vocabulary(task):
    """Sorted token and label vocabularies: sorted so ids are reproducible."""
    tokens = sorted(VOCABULARY_A if task == 'A' else VOCABULARY_B)
    labels = sorted(VALUES if task == 'A' else CANDIDATES)
    return tokens, labels


def encode(examples, tokens, labels):
    """Pack one split into the binary format above."""
    token_id = {name: i for i, name in enumerate(tokens)}
    label_id = {name: i for i, name in enumerate(labels)}
    pad_id = token_id['PAD']
    seq_len = max(len(example.tokens) for example in examples)
    body = bytearray()
    for example in examples:
        ids = [token_id[name] for name in example.tokens]
        ids += [pad_id] * (seq_len - len(ids))
        body += struct.pack('<%di' % seq_len, *ids)
    body += struct.pack('<%di' % len(examples),
                        *(label_id[example.target] for example in examples))
    header = MAGIC + struct.pack('<7I', FORMAT_VERSION, len(examples), seq_len,
                                 len(tokens), len(labels), pad_id, 0)
    return bytes(header + body), seq_len, pad_id


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', default=os.path.join('data', 'm7'),
                        help='output directory (default data/m7)')
    parser.add_argument('--force', action='store_true',
                        help='overwrite existing frozen artifacts')
    arguments = parser.parse_args()

    paths = [os.path.join(arguments.out, '%s_%s.bin' % (task.lower(), split))
             for task in ('A', 'B') for split in SPLITS]
    paths.append(os.path.join(arguments.out, 'manifest.json'))
    existing = [path for path in paths if os.path.exists(path)]
    if existing and not arguments.force:
        raise SystemExit('refusing to overwrite frozen artifacts (%d exist, e.g. %s); '
                         'pass --force' % (len(existing), existing[0]))
    os.makedirs(arguments.out, exist_ok=True)

    files = []
    for task in ('A', 'B'):
        splits = make_splits_reduced(task)
        hashes = [{token_hash(example.tokens) for example in split}
                  for split in splits.values()]
        disjoint = all(left.isdisjoint(right) for left, right in combinations(hashes, 2))
        print('task %s: splits pairwise disjoint by token_hash: %s (%d unique inputs)'
              % (task, disjoint, len(set().union(*hashes))))
        assert disjoint, 'task %s: splits share an input' % task
        tokens, labels = vocabulary(task)
        for split in SPLITS:
            blob, seq_len, pad_id = encode(splits[split], tokens, labels)
            name = '%s_%s.bin' % (task.lower(), split)
            with open(os.path.join(arguments.out, name), 'wb') as handle:
                handle.write(blob)
            digest = sha256(blob).hexdigest()
            files.append({
                'file': name,
                'task': task,
                'split': split,
                'n_rows': len(splits[split]),
                'seq_len': seq_len,
                'vocab': len(tokens),
                'n_class': len(labels),
                'pad_id': pad_id,
                'bytes': len(blob),
                'sha256': digest,
            })
            print('%-20s rows %5d  seq_len %3d  vocab %3d  n_class %d  pad %2d  %s'
                  % (name, len(splits[split]), seq_len, len(tokens), len(labels),
                     pad_id, digest))

    manifest = {
        'preset': PRESET,
        'note': NOTE,
        'format': {'magic': MAGIC.decode('ascii'), 'version': FORMAT_VERSION,
                   'endianness': 'little', 'element': 'i32'},
        'generator_version': GENERATOR_VERSION,
        'seed': SEED,
        'difficulty': {
            'task_A': {'keys': list(A_KEYS), 'distractors': list(A_DISTRACTORS),
                       'spec_suggestion': {'keys': [2, 8], 'distractors': [0, 32]}},
            'task_B': {'informative_clues': list(B_INFORMATIVE),
                       'neutral_delay': list(B_DELAY)},
            'length_split': {'task_A_keys': list(A_LENGTH_KEYS),
                             'delay': list(LENGTH_DELAY)},
        },
        'sizes': {'train': TRAIN_SIZE, 'validation': SPLIT_SIZE,
                  'composition': SPLIT_SIZE, 'length': SPLIT_SIZE},
        'files': files,
    }
    path = os.path.join(arguments.out, 'manifest.json')
    with open(path, 'w', newline='\n') as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print('wrote %s' % path)


if __name__ == '__main__':
    main()
