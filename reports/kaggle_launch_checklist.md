# Kaggle Launch Checklist — Agent Failure Atlas 2026

Status as of this final launch-preparation pass. All BEFORE PUBLISHING
items are checked off and verified by direct inspection (validator,
pytest, file checksums, notebook re-execution) — not assumed from a prior
report.

## BEFORE PUBLISHING

- [x] Dataset files finalized — 10 CSVs in `data/`, byte-identical to a
      fresh independent regeneration (verified by checksum diff this pass)
- [x] Title finalized — "Agent Failure Atlas 2026: AI Agent Trajectory,
      Failure & Recovery Benchmark" (brand: "Agent Failure Atlas 2026")
- [x] Description finalized — `docs/kaggle_description.md`, opens with
      the synthetic-benchmark disclosure, no unverified superlative claims
- [x] Synthetic disclosure visible — present near the top of both
      `README.md` and `docs/kaggle_description.md`
- [x] Thumbnail finalized — `assets/kaggle_thumbnail.png`, "AI AGENTS" /
      "FAILURE + RECOVERY" dominant, simplified 3-node motif, no tiny
      unreadable statistics
- [x] Tags finalized — AI, Artificial Intelligence, Agents, LLM, Machine
      Learning, NLP, Benchmark, Evaluation, Reasoning, Generative AI, RAG,
      Tool Use (see `docs/kaggle_description.md`)
- [x] License finalized — MIT (code) + CC BY 4.0 (data), consistent
      across `LICENSE`, README, and Kaggle description
- [x] Citation finalized — present in README and Kaggle description,
      placeholder left only for the post-publication Kaggle URL
- [x] Notebooks tested — all 3 re-executed fresh this pass, 0 errors, 0
      stale outputs, 0 hardcoded local paths (explicitly grepped for)
- [x] README finalized — all 21 required topics present and
      distinguishable (verified against the section list this pass;
      Evidence and Student Use Cases were split into their own headings
      during this audit)
- [x] Publication manifest finalized — `reports/publication_manifest.md`,
      updated this pass with the market-research and launch-planning files
- [x] Validation passed — 107/107 (re-run this pass)
- [x] Tests passed — 13/13 (re-run this pass)

## DURING PUBLICATION

*(For the human publisher to execute — not automatable from here.)*

- [ ] Upload correct files (see `reports/publication_manifest.md` —
      "Required Kaggle files" section only; do not upload the
      "Optional supporting repository files")
- [ ] Verify dataset title matches exactly: "Agent Failure Atlas 2026: AI
      Agent Trajectory, Failure & Recovery Benchmark"
- [ ] Verify description renders correctly (headings, code blocks, the
      opening synthetic-disclosure blockquote)
- [ ] Verify thumbnail displays correctly at both full size and card/list
      size
- [ ] Verify tags match the finalized list
- [ ] Verify license is set to CC BY 4.0 for the dataset
- [ ] Verify file preview (spot-check a few rows of each CSV render
      correctly in Kaggle's own viewer)
- [ ] Verify notebooks attach/run correctly on Kaggle's own kernel
      environment (Kaggle's runtime may differ slightly from local —
      confirm before considering this step done)
- [ ] Publish

## AFTER PUBLICATION

- [ ] Verify the public page (open the live URL, not a preview)
- [ ] Open the dataset from a fresh browser/session (logged out, or
      incognito) to see exactly what a first-time visitor sees
- [ ] Verify download works end-to-end
- [ ] Verify each notebook works when run fresh from the published dataset
      (not from local files)
- [ ] Publish the discussion post (`reports/launch_copy.md` has the draft)
- [ ] Monitor comments and respond promptly
- [ ] Record first-hour metrics (use `reports/launch_metrics_template.csv`)
- [ ] Record 6-hour metrics
- [ ] Record 24-hour metrics
- [ ] Record 7-day metrics

## Reference

- Launch timing: `reports/distribution_plan.md`
- Launch copy (Kaggle discussion, LinkedIn, X, GitHub, Reddit):
  `reports/launch_copy.md`
- Realistic vs. stretch targets: `research/launch_decision.md`
- Full quality/readiness status: `reports/quality_self_assessment.md`,
  `reports/final_quality_report.md`
