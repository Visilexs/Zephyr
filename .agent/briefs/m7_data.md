# M7 data pipeline: frozen datasets and a native loader

Two deliverables. Both are mechanical; nothing here needs design judgement,
but exactness matters and every claim must be checked by running something.

Repo: `C:\Users\Visil\Documents\Ultra important project\Zephyr`
Reference generator: `tools/ml_reference/tasks.py` (already verified -- do
not modify its generation logic, and do not rewrite it in Zephyr).

## Deliverable 1: `tools/ml_reference/freeze_datasets.py`

A new script that generates the M7 datasets once and writes them to disk as
frozen artifacts, plus a manifest.

The predeclared M7 preset, which is deliberately smaller than the spec's
suggested difficulty and must be recorded as such in the manifest:

- Task A: n = 2..4 keys, d = 0..8 distractors  (the spec suggests n=2..8,
  d=0..32; we are declaring a reduced budget)
- Task B: 2..4 informative clues, neutral delays as `tasks.py` already does
- Splits and sizes: train 4096, validation 2048, composition 2048,
  length 2048 -- i.e. `make_splits`'s existing defaults
- Seed for data generation: 20260921, fixed and recorded

Output directory: `data/m7/` (create it). One file per task per split:
`data/m7/<task>_<split>.bin`.

Binary format, little-endian, documented in a comment at the top of both the
writer and the reader:

```
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
```

Also write `data/m7/manifest.json` containing, for every file: the task, the
split, row count, sequence length, vocab sizes, pad id, the SHA-256 of the
file, and the declared difficulty parameters and generation seed. Include a
top-level `"preset": "m7-reduced"` and a human-readable note that the
difficulty is below the spec's suggestion by declaration.

Requirements on the script:
- It must be deterministic: running it twice produces byte-identical files.
  Prove this by running it twice and comparing SHA-256, and show that output.
- It must refuse to overwrite existing files unless `--force` is passed,
  because these are frozen artifacts.
- Splits must be disjoint. Assert it in the script, using the same
  deduplication notion `tasks.py` already uses, and print the check result.

## Deliverable 2: `lib/ml/dataset.zeph`

A native loader for that format. No Python at run time.

```zephyr
struct Dataset {
    tokens: Tensor,   // I64, [n_rows, seq_len]
    targets: [int],   // length n_rows
    seq_len: int,
    vocab: int,
    n_class: int,
    pad_id: int,
}

fn dataset_load(path: str) -> Dataset
fn dataset_batch(d: Dataset, start: int, count: int) -> Dataset   // a row slice
```

Notes:
- Read the file with the existing helpers in this repo; look at how other
  code reads files before inventing anything. Note that `read_file` panics on
  a missing path rather than returning empty, so check existence first the
  way `lib/ml/gpu.zeph` does (`GetFileAttributesA` via `win(...)`).
- Every header field must be validated with a message naming the file and
  what was wrong: bad magic, unknown version, a row/element count that does
  not match the file size, a token id outside the vocabulary, a target
  outside the class count. A truncated file must be rejected, not read
  partially.
- `dataset_batch` returns rows [start, start+count) and must panic on an
  out-of-range request rather than clamping.

## Deliverable 3: `tests/ml/dataset_test.zeph`

A test suite in the style of the existing ones in `tests/ml/` -- read
`tests/ml/opt_test.zeph` first and follow its conventions exactly: a `chk`
counter, a final `print("dataset: N checks passed")`, and rejection cases run
in child processes via `CreateProcessA` because a panic cannot be caught in
process.

It must cover, at minimum:
- Every file in `data/m7/` loads, and its row count, sequence length and
  vocabulary match `manifest.json`.
- Every token id is inside the vocabulary and every target inside the class
  count, checked over all rows, not a sample.
- A batch slice returns exactly the requested rows and they equal the same
  rows read from the whole dataset.
- Malformed files are rejected, each in its own child process, each case
  built by corrupting a real file in the scratch directory: bad magic,
  unknown version, truncated payload, a token id out of range, a target out
  of range, an out-of-range batch request.
- The suite must fail if `data/m7/` is missing, with a message naming
  `freeze_datasets.py`, rather than passing vacuously.

Register it in `tests/run_tests.ps1` next to the `"ml-opt"` and `"ml-fusion"`
entries, following their exact format.

**Warning about that file.** Writing `tests\ml\fusion_test.zeph` through a
Python string has already corrupted this repo once: `\f` becomes a formfeed.
Build any path string in that file without literal backslash escapes (use
`chr(92)`), and after writing, read the bytes back and assert no control
characters below 0x20 other than CR and LF are present.

## Definition of done

- `python tools/ml_reference/freeze_datasets.py` produces `data/m7/` and
  running it twice gives identical hashes. Show the command and its output.
- `.\zc.exe --rt tests\ml\dataset_test.zeph out.exe` compiles and the binary
  prints `dataset: N checks passed` with N reported. Show it.
- `git status --short` shows exactly the intended files and nothing else.
- Report the actual N, the dataset hashes, and anything you could not do.
  If a check does not pass, say so plainly rather than adjusting the check.

Do not touch `lib/ml/ops.zeph`, `lib/ml/autograd.zeph`, `lib/ml/phase_ad.zeph`
or `lib/ml/ir.zeph` -- other work is in flight on those files.
