# Reproducibility — Agent Failure Atlas 2026 (v2)

## Generation pipeline

The full dataset is produced by one command:

```bash
python src/generation/generate_data.py --n-tasks 1400 --runs-per-task 4 --failure-prob 0.02 --seed 42
```

This writes all **ten** CSVs to `data/` (nine in v1; `evidence.csv` is new
in v2). See `docs/methodology.md` for what each stage of the pipeline
does. Note `--failure-prob` is now a small **base** rate (default `0.02`)
that gets additively adjusted per-step by task/agent features (see
`docs/methodology.md`, "Feature-driven failure probability") — it is not
directly comparable to v1's `--failure-prob` (default `0.46`), which was
the actual per-run probability with no per-step modulation.

## Random seeds

The entire pipeline is driven by a single `numpy.random.default_rng(seed)`
instance (`--seed`, default `42`), threaded explicitly through every
sampling call (task selection, agent assignment, trajectory length,
failure injection, recovery strategy/outcome, latency/token sampling).
There is no other source of randomness (no unseeded `random.*` calls, no
wall-clock-dependent behavior in the data values themselves — synthetic
timestamps are derived deterministically from cumulative seeded offsets).
**Same `--seed` always produces byte-identical CSVs.**

## Environment

```
Python: 3.13
Core dependencies: numpy>=2.0,<3.0, pandas>=2.2,<3.0  (see requirements.txt)
Notebook execution: jupyter, nbconvert, jupytext (percent-format .py <-> .ipynb)
```

No GPU, no external network access, and no API keys are required to
regenerate the dataset or re-run any notebook.

## Model versions

Not applicable — this release does not call any live model API. The
`agents.csv` table lists **simulated** model/provider identifiers used
purely as generation parameters (e.g. to vary trajectory length
distribution or recovery base rates by "model family" in a future
version); they are not references to actual API-versioned models. See
`docs/methodology.md` and `docs/data_governance.md`.

## Configuration

All generation parameters are CLI flags on `generate_data.py`:

| flag | default | effect |
|---|---|---|
| `--n-tasks` | 900 | number of distinct tasks generated |
| `--runs-per-task` | 4 | max agent runs per task (actual count sampled 1..N) |
| `--failure-prob` | 0.02 | **base** per-step failure probability before feature-driven additive adjustments (see methodology.md) |
| `--seed` | 42 | RNG seed |
| `--out` | `data/` | output directory |

The published v2 release used `--n-tasks 1400 --runs-per-task 4 --failure-prob 0.02 --seed 42`.

## Validation

After generation, run:

```bash
python src/validation/validate.py
```

or the equivalent pytest suite:

```bash
pytest tests/
```

Both check referential integrity, primary-key uniqueness, required-field
nulls, enumeration membership against the canonical taxonomy
(`src/generation/taxonomy.py`), trajectory sequencing, numeric bounds,
multi-failure ordering, cascade-edge validity, recovery-attempt ordering,
and label-leakage detection (107 checks / 13 tests as of this release),
and write `reports/final_quality_report.md`.

## Export process

CSV export is a direct `DataFrame.to_csv(..., index=False)` call per table
in `generate_data.py` — no post-processing, filtering, or manual editing
occurs between generation and the published files. `docs/taxonomy.md` is
itself generated from `src/generation/taxonomy.py` (the same module the
generator and validator import), so taxonomy documentation cannot drift
from the taxonomy actually used to label the data.

## Limitation on complete reproduction

None specific to this release: because generation uses no proprietary
model API, the pipeline is fully and exactly reproducible by anyone with
the published code and the stated Python/dependency versions. This is a
deliberate methodological choice — see `docs/methodology.md` for the
tradeoffs this implies about what the dataset does and does not represent.
