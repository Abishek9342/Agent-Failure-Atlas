# Publication Manifest — Agent Failure Atlas 2026 (v2)

Exact file sizes measured directly from the final repository at audit
time. Lists what would be uploaded to Kaggle versus what stays as
supporting development material.

## Required Kaggle files

### Dataset files (upload as the Kaggle Dataset)

| File | Purpose | Size | Format |
|---|---|---:|---|
| `data/tasks.csv` | Core table: one row per task | 681,235 B (~665 KB) | CSV |
| `data/agents.csv` | Reference table: agent configurations | 1,129 B | CSV |
| `data/tools.csv` | Reference table: tool catalogue | 1,314 B | CSV |
| `data/taxonomy.csv` | Reference table: machine-readable failure taxonomy | 6,533 B | CSV |
| `data/agent_runs.csv` | Core table: one row per trajectory | 620,799 B (~606 KB) | CSV |
| `data/trajectory_steps.csv` | Core table: one row per execution step | 8,345,042 B (~8.0 MB) | CSV |
| `data/failure_events.csv` | Core table: one row per diagnosed failure | 942,933 B (~921 KB) | CSV |
| `data/recovery_events.csv` | Core table: one row per recovery attempt | 518,050 B (~506 KB) | CSV |
| `data/evaluations.csv` | Core table: one row per run's evaluation | 184,193 B (~180 KB) | CSV |
| `data/evidence.csv` | Core table: one row per claim/evidence relationship | 1,571,350 B (~1.5 MB) | CSV |

**Total data payload: ~12.5 MB** across 10 CSVs.

### Description, dictionary, license, citation

| File | Purpose | Size | Format |
|---|---|---:|---|
| `README.md` | Dataset overview, stats, schema, quick start | 17,696 B | Markdown |
| `docs/kaggle_description.md` | Source text for the Kaggle description field | 7,462 B | Markdown |
| `docs/data_dictionary.md` | Every field in every table documented | 20,066 B | Markdown |
| `docs/taxonomy.md` | Full failure/recovery taxonomy + severity rubric + cascades | 14,037 B | Markdown |
| `LICENSE` | MIT (code) + CC BY 4.0 (data) | 1,310 B | Text |

### Thumbnail

| File | Purpose | Size | Format |
|---|---|---:|---|
| `assets/kaggle_thumbnail.png` | 16:9 Kaggle dataset thumbnail — final "AI AGENTS / FAILURE + RECOVERY" design | 42,926 B (~42 KB) | PNG |

### Sample data (optional but recommended for quick preview)

| File | Purpose | Size | Format |
|---|---|---:|---|
| `data/samples/*_sample.csv` (10 files) | First 25 rows of each table, for quick preview without downloading full CSVs | 4,804–12,245 B each | CSV |

### Notebooks (upload as Kaggle Notebooks attached to the dataset)

| File | Purpose | Size | Format |
|---|---|---:|---|
| `notebooks/01_exploratory_analysis.ipynb` | Hero notebook: "How AI Agents Fail" | 555,728 B (~543 KB) | Jupyter notebook (with outputs) |
| `notebooks/02_predict_agent_failure.ipynb` | "Can We Predict Agent Failure?" — ML baseline | 124,412 B (~122 KB) | Jupyter notebook (with outputs) |
| `notebooks/03_recovery_analysis.ipynb` | "Can AI Agents Recover From Failure?" | 275,698 B (~269 KB) | Jupyter notebook (with outputs) |

### Kaggle discussion (post manually after publication, not uploaded as a file)

| File | Purpose |
|---|---|
| `docs/kaggle_discussion_post.md` | Draft text for the first discussion post ("What Is the Hardest AI-Agent Failure to Recover From?") |
| `reports/launch_copy.md` | Ready-to-use copy for the Kaggle discussion + LinkedIn/X/GitHub/Reddit launch posts (see also `reports/distribution_plan.md`) |

## Optional supporting repository files

Not part of the Kaggle dataset/notebook upload — kept in the source
repository for reproducibility, governance, and development history.

| File | Purpose |
|---|---|
| `docs/methodology.md` | Full generation pipeline + exact metric formulas (linked from README, not re-uploaded separately to Kaggle) |
| `docs/data_governance.md` | Licensing rationale, synthetic-data disclosure, prohibited interpretations |
| `docs/reproducibility.md` | Exact regeneration commands, seed, environment |
| `research/competitor_analysis.md` | Original technical competitor/taxonomy comparison |
| `research/final_kaggle_market_research.md` | Market-research round 1 (26-part brief, ~35 searches) |
| `research/kaggle_competitor_matrix.csv` | Round 1 structured competitor table |
| `research/final_kaggle_market_research_v2.md` | Market-research round 2 — independently re-derived, not a copy of round 1 |
| `research/kaggle_competitor_matrix_v2.csv` | Round 2 structured competitor table |
| `research/launch_decision.md` | Self-contained launch-decision summary from round 2 |
| `reports/final_quality_report.md` | Auto-generated validation report (107/107 checks) |
| `reports/quality_self_assessment.md` | Honest internal quality scoring |
| `reports/publication_manifest.md` | This file |
| `reports/kaggle_launch_checklist.md` | Pre/during/after-publication checklist |
| `reports/distribution_plan.md` | Legitimate, no-fake-engagement launch/distribution plan |
| `reports/launch_copy.md` | Ready-to-use launch copy (not auto-posted) |
| `reports/launch_metrics_template.csv` | Blank template for recording actual post-launch metrics |
| `src/generation/generate_data.py`, `src/generation/taxonomy.py` | Generation pipeline source (source-of-truth for taxonomy docs) |
| `src/validation/validate.py` | Validation suite source |
| `tests/test_dataset.py` | pytest suite source |
| `notebooks/*.py` | Percent-format source for each notebook (jupytext), used to author/maintain the `.ipynb` files |
| `assets/make_thumbnail.py` | Reproducible thumbnail-generation script |
| `requirements.txt`, `pyproject.toml` | Python dependency/tooling specification |
| `.gitignore` | Standard Python/notebook ignore rules |

**Rationale for the split:** Kaggle datasets are meant to be consumed via
the published CSVs, notebooks, description, and thumbnail — a stranger
downloading the dataset does not need the generation source code,
research notes, or internal quality-scoring documents to use it. Those
stay in the source repository (and are still referenced by relative link
from the README for anyone who wants to inspect or reproduce the
pipeline) rather than cluttering the Kaggle-facing package.
