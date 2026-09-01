# Competitor & Market Analysis — Agent Failure Atlas 2026

## Methodology

Research was conducted on **2026-08-27** using web search (no direct Kaggle API
access; Kaggle dataset/competition pages were queried via search snippets and,
where possible, direct page fetch — several Kaggle pages are JS-rendered and
did not return full body text to the fetch tool, in which case findings are
limited to what was verifiable in search-result snippets and clearly marked
as such).

Search covered: named lookups for specific projects the user asked about
("Agent Arena," "AI Agent Security," "AgentRx," "ATBench," "FACTS,"
"AgentEval"), plus broader terms ("agent trajectory dataset kaggle," "LLM
agent failure benchmark," "tool use failure dataset," "agent evaluation
benchmark 2026," "AgentBench," "ToolBench," "AgentOps benchmark," "WebArena,"
"SWE-bench agent trajectories," "RAG agent evaluation," "agent
self-correction recovery benchmark," "GAIA benchmark," "Holistic Agent
Leaderboard," "AgentAtlas," "TRAIL").

**Caveats:**
- Findings reflect what is verifiable via public web search on this date.
  Kaggle view/download/vote counts are generally not exposed in search
  snippets and are **not reported** here unless a number appeared explicitly
  in a fetched/quoted source — per the project's rule against fabricating
  unverifiable metrics.
- "Not found" below means no credible source surfaced in multiple search
  attempts — it does not prove non-existence, only that it isn't
  discoverable through this method.
- Paper/arXiv IDs and reported statistics are quoted as they appeared in
  search results; they have not been independently re-verified against the
  primary PDF in every case.

---

## Landscape summary

The agent-evaluation space has grown extremely fast between 2024 and 2026.
Foundational trajectory-style benchmarks (AgentBench, WebArena, GAIA,
ToolBench/ToolLLM, SWE-bench and its many trajectory-corpus derivatives)
established the idea of scoring an agent's full action sequence rather than
just a final answer. Since 2025 a second wave has specifically targeted
**failure diagnosis** rather than success measurement: TRAIL (Patronus AI),
AgentRx (Microsoft Research), ATBench (safety-focused trajectory benchmark),
ToolFailBench, AgentErrorBench, "Where LLM Agents Fail and How They Can
Learn From Failures," and AgentAtlas (a diagnostic taxonomy/audit paper) all
converge on the same insight this project is built around: pass/fail labels
hide the mechanics of *why* and *where* an agent went wrong, and closing that
gap requires a step-level, taxonomy-labeled trace of the whole trajectory.

Almost everything found in this category is (a) a research paper with a
narrow, single-purpose benchmark released alongside it, (b) sourced from
**real model transcripts** (GAIA, SWE-bench, OpenTelemetry/OpenInference
traces, live tool calls), and (c) scoped to one or two domains (coding,
web navigation, safety red-teaming). None of the projects found combine a
full relational schema (tasks → runs → steps → failures → recoveries →
evaluations) with an explicit, documented failure *and* recovery taxonomy
in one Kaggle-native, CSV-based, synthetic-but-reproducible package. The one
directly comparable Kaggle artifact — "LLM Agent Failure Analysis Benchmark
Dataset" by sunil123kumar — appears to be a single flat table of ~1,500
samples, not a multi-table relational trajectory schema.

Kaggle itself has recently invested in this space at the competition level:
"AI Agent Security – Multi-Step Tool Attacks" (partnered with OpenAI, Google,
IEEE, $50,000 prize pool, live in mid-2026) is a real, currently-running
red-teaming competition, confirming Kaggle's own strategic interest in
agent-failure/security content — but it is a live adversarial competition
against a hosted agent, not a downloadable structured dataset, so it doesn't
compete directly with a static benchmark dataset like this one.

---

## Detailed findings

### Items specifically requested for verification

| Query | Verdict | Notes |
|---|---|---|
| Kaggle "Agent Arena" dataset | **Not found as a specific dataset by that name.** | Kaggle does run a "Game Arena" (head-to-head model/agent competition in games, e.g. chess) and hosts unrelated "*-arena" items (`long-range-arena`, `long-range-arena-processed`, `chatbot-arena-conversations`). None of these is an "Agent Arena" trajectory/failure dataset. Do not claim it exists. |
| Kaggle "AI Agent Security" competition | **Real — confirmed.** | Full title: **"AI Agent Security – Multi-Step Tool Attacks"**, https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks. Partnered with OpenAI, Google, and IEEE; $50,000 prize pool; a red-teaming challenge to craft multi-step tool-use attacks against defended agents, scored against live guardrails in a deterministic offline benchmark. Live/active around mid-2026 per an X/Kaggle post and multiple public solution notebooks. This is a **competition** (adversarial, leaderboard-scored), not a downloadable structured trajectory dataset. |
| "AgentRx" | **Real — confirmed, high relevance.** | Microsoft Research, published ~March 2026. arXiv 2602.02475: *"AgentRx: Diagnosing AI Agent Failures from Execution Trajectories."* Open-source (github.com/microsoft/agentrx). Automatically localizes the critical failure step in a failed trajectory via synthesized invariants + an LLM judge, classifying failures into a **10-category taxonomy**. Ships a benchmark of **115 failed trajectories** across structured API workflows, incident management, and open-ended web/file tasks. Reports 23.6-point and 19.4-point absolute improvements in localization/cause-identification over baselines (as stated by Microsoft's own blog/paper summary — not independently re-verified here). |
| "ATBench" | **Real — confirmed.** | arXiv 2604.02022, *"ATBench: A Diverse and Realistic Agent Trajectory Benchmark for Safety Evaluation and Diagnosis."* **1,000 trajectories** (503 safe / 497 unsafe), averaging **9.01 turns** and **3.95k tokens** per trajectory, **1,954 invoked tool calls** drawn from a pool of **2,084 available tools**. Organizes risk along risk-source / failure-mode / real-world-harm dimensions; built via a long-context delayed-trigger protocol plus rule-based + LLM-based filtering and full human audit. Domain extensions ATBench-Claw and ATBench-Codex exist (arXiv 2604.14858). GitHub: github.com/LiYu0524/ATbench. |
| "FACTS" / grounding benchmarks | **Real — confirmed (Google DeepMind).** | *FACTS Grounding*: arXiv 2501.03200 / deepmind.google blog. **1,719 examples** (860 public + 859 private), contexts up to 32,000 tokens, spanning medicine, law, technology, finance, retail. Excludes math/creativity/complex-reasoning tasks — purely about whether long-form answers are grounded in a supplied source document. Hosted as a live leaderboard on Kaggle (`kaggle.com/benchmarks/google/facts-grounding` and a broader `kaggle.com/benchmarks/google/facts` "FACTS Benchmark Suite"). This is a **factuality/grounding** benchmark for single-turn long-form QA, not a multi-step agent trajectory/failure-recovery benchmark — a genuinely different task shape from this project. |
| "AgentEval" | **Exists, but not as an agent-*failure* dataset — different tool, easy to confuse.** | GitHub `AgentEvalHQ/AgentEval` is a **.NET toolkit** for AI agent evaluation (tool-usage validation, RAG quality metrics, stochastic evaluation, model comparison) — positioned as the .NET analog of RAGAS/PromptFoo/DeepEval for Python. Separately, "AgentEval Benchmark Suite" appears in secondary sources (emergentmind.com) as a more generic framework concept (process-oriented success/progress/checklist metrics, `reset()`/`step()` environment abstraction) — this looks like a descriptive/aggregator framing rather than one canonical released benchmark, and the primary source for that framing was not independently confirmed. Neither is a structured, taxonomy-labeled failure/recovery **dataset**. |

### Broader landscape — real projects found

| Project | Source | Purpose | Size (only where verified) | Structure / task types | Labels | Real vs. synthetic |
|---|---|---|---|---|---|---|
| **AgentBench** | arXiv 2308.03688, github.com/THUDM/AgentBench, ICLR'24 | First broad benchmark evaluating LLMs as agents | 8 environments, 29 LLMs evaluated (as reported) | Multi-environment: OS, DB, web shopping, web browsing, knowledge graphs, card games, etc. | Environment-specific success metrics | Environment-driven interaction, not failure-taxonomy labeled |
| **WebArena** | arXiv 2307.13854, github.com/web-arena-x/webarena | Realistic, reproducible web environment for autonomous agents | **812 tasks** across 4 domains (e-commerce, forums, dev collaboration, CMS) | Full functional websites; HTML/DOM or accessibility-tree observations, compound action space | Task success only (best GPT-4 agent: 14.41% vs. 78.24% human) | Real interactive environment, not synthetic |
| **GAIA** | arXiv 2311.12983 | Benchmark for "General AI Assistants" | **466 questions**, 3 difficulty levels | Reasoning, multimodal, web navigation, tool use | Pass/fail on final answer, tiered by step-count/tool-count difficulty | Real, human-authored questions |
| **ToolBench / ToolLLM** | OpenReview, github.com/beijixiong1/ToolLLM | Tool-use / API-call learning and evaluation | **16,464 real RESTful APIs** (49 categories, RapidAPI Hub), **126,000+** instruction–solution path pairs | Single- and multi-tool API call sequencing | Solution-path correctness; generalization splits (unseen instructions/tools/categories) | Real APIs; LLM-generated (ChatGPT) instructions and solution paths |
| **TRAIL** | arXiv 2505.08638, Patronus AI, huggingface.co/datasets/PatronusAI/TRAIL | Trace-level error localization/debugging benchmark | **148 annotated traces**, **841 unique errors** | Built from real GAIA and SWE-Bench task executions (o3-mini, Claude); OpenTelemetry/OpenInference traces | Taxonomy spans reasoning errors, system-execution errors, planning/coordination errors | **Real** model transcripts, human-annotated |
| **AgentRx** | arXiv 2602.02475, Microsoft Research | Automated root-cause localization + failure classification | 115 failed trajectories (benchmark release) | Structured API workflows, incident management, open-ended web/file tasks | 10-category grounded failure taxonomy | Real agent failures diagnosed by the framework |
| **ATBench** (+ Claw/Codex variants) | arXiv 2604.02022 / 2604.14858 | Long-horizon agent **safety** trajectory benchmark | 1,000 trajectories (503 safe/497 unsafe) | Risk-source × failure-mode × harm-type taxonomy; heterogeneous tool pools | Safe/unsafe + taxonomy-stratified labels | Constructed protocol with human audit (methodology not fully "synthetic-from-scratch" like ours) |
| **ToolFailBench** | arXiv 2607.04686 | Diagnosing tool-use failures specifically | **1,000 tasks** across finance, medicine, law, cybersecurity, real estate | Labeled failure classes: Tool-Skip, Result-Ignore, Output-Fabrication, Unnecessary-Tool-Use | 4-way tool-use failure label set; best model reaches 86.33% "Clean Tool-Use Rate" | Not specified as synthetic vs. real in available snippets |
| **AgentErrorBench / "Where LLM Agents Fail..."** | arXiv 2509.25370, OpenReview PFR4E8583W | Systematically annotated failure trajectories | **200 failed rollouts** across ALFWorld, GAIA, WebShop | Failure modes across memory, reflection, planning, action, system-level ops | Modular failure-mode classification | Real rollouts from existing agent environments |
| **Failing Tools** | OpenReview j7YsSnA64D | Benchmarks agent recovery under **injected runtime tool failures** | Not stated in available snippets | Multi-turn tool-calling with injected transient/permanent faults | Detect / distinguish / retry / fallback behaviors | Deliberately injected (synthetic) failures into otherwise real tool-calling scenarios — closest analog in spirit to this project's recovery-event modeling |
| **AgentHallu** | (via search snippet, not independently opened) | Step-level hallucination attribution for agents | **693 trajectories**, 5 domains | Step-level attribution of hallucination causes | Hallucination-type taxonomy | Not confirmed real vs. synthetic from available snippet |
| **AgentAtlas** (paper) | arXiv 2605.20530 | Diagnostic vocabulary + audit protocol, *not* a released public dataset | Illustrative-only: 1,342-item **synthetic** demo set | 6-state control-decision taxonomy (Act/Ask/Refuse/Stop/Confirm/Recover) + trajectory-failure vocabulary; audits 15 existing benchmarks for taxonomy coverage | Control-decision states + primary error source/downstream impact | Explicitly synthetic and explicitly **not** a public benchmark release (per the paper's own framing) — name-adjacent to this project but a different artifact (a coverage audit of *other* benchmarks, not a trajectory dataset itself) |
| **Holistic Agent Leaderboard (HAL)** | arXiv 2510.11977, ICLR 2026 | Infrastructure/harness for standardized, reproducible agent evaluation across benchmarks | 21,730 rollouts, 9 models, 9 benchmarks, ~$40,000 total cost (as reported by the paper) | Cross-benchmark harness spanning coding, web navigation, science, customer service | Cost-controlled, automated log analysis; not a taxonomy of failure types per se | Aggregates results from existing (mostly real) benchmarks; not itself a trajectory dataset |
| **SWE-bench trajectory corpora** (SWE-agent-trajectories, SWE-smith-trajectories, SWE-rebench-OpenHands, Open-SWE-Traces) | Hugging Face (nebius/, SWE-bench/) | Training/eval corpora of full coding-agent trajectories | 80,036 / 5,017 / (unspecified) / 207,489 trajectories respectively (as stated on their HF dataset pages) | GitHub issue resolution; multi-turn tool use in a coding sandbox | Resolved/unresolved on SWE-bench Verified; no general failure-mode taxonomy | Real agent runs (various open-weight/closed models), single domain (software engineering) |
| **"LLM Agent Failure Analysis Benchmark Dataset"** (Kaggle) | kaggle.com/datasets/sunil123kumar/ai-agent-failure-benchmark-dataset | Closest direct Kaggle competitor found | **1,500 samples** (per search snippet; posted ~June 27, 2026) | Not independently verified — page could not be fully fetched (Kaggle dataset pages are JS-rendered); appears to be a single benchmark table, not a multi-table relational schema | Unknown/unverified from available access | Unknown/unverified — treat size and any other detail beyond "1,500 samples" as unconfirmed until manually checked on Kaggle |
| **RAGCap-Bench** | arXiv 2510.13910 | Benchmarks LLM capabilities within agentic RAG pipelines | Not stated in available snippets | Retrieval-augmented agent capability testing | Capability-level scoring, not a failure taxonomy | Not confirmed synthetic vs. real |

### Notable near-misses / adjacent-but-different

- **Kaggle "Game Arena"** — real, but a live head-to-head model competition in games (e.g., chess), unrelated to failure-taxonomy trajectory data.
- **KaggleBench / MLAgentBench / MLE-Bench / Agent K** — real, but these evaluate agents *on* Kaggle-style ML competitions (data science task completion), not agent trajectory failure analysis as a dataset artifact.
- **AgentOps (AgentOps-AI)** — real open-source observability/monitoring SDK (github.com/AgentOps-AI/agentops) with session replay, cost tracking, and "1,000+ evals" for benchmarking — a tool/product, not a downloadable dataset.

---

## What's missing in the current landscape / our differentiation

Based on what was found (and being explicit about what was *not* verified):

1. **Relational depth.** Nearly every competing artifact found is a single flat table or a corpus of raw traces (JSON/OpenTelemetry logs). None combine, in one package, the explicit six-table relational chain this project uses — `tasks → agent_runs → trajectory_steps → failure_events → recovery_events`, plus `evaluations`, `agents`, `tools`, and a machine-readable `taxonomy` table with resolvable foreign keys. This is a structural difference, not just a size difference.

2. **Recovery is usually an afterthought, not a first-class table.** "Failing Tools" and PALADIN/SENTINEL-style papers study recovery, but as a research paper's evaluation protocol, not as a directly downloadable, documented dataset with a `recovery_events` table mapping specific strategies (retry, alternative_tool, replan, rollback, etc.) to specific failure categories with recorded outcomes and cost (extra steps/tokens/latency). This project makes that mapping into structured, queryable data.

3. **Taxonomy transparency and reproducibility.** AgentRx (10 categories), ATBench (risk/failure/harm dimensions), and AgentErrorBench each define their own taxonomy, but none publish a `taxonomy.csv` cross-referenced 1:1 against every labeled event in a public, from-scratch-reproducible pipeline. This project's taxonomy (8 categories × 30 sub-types, plus 9 recovery strategies) is generated from a single source-of-truth script (`src/generation/taxonomy.py`) that both the generator and validator import — so the published docs cannot drift from the data. That specific reproducibility guarantee was not found (verified) elsewhere in the search.

4. **Synthetic-and-honest, not synthetic-and-hidden.** Most competing benchmarks are sourced from real model transcripts (TRAIL, AgentErrorBench, SWE-bench corpora) or partially real protocols with human audit (ATBench). This project is openly synthetic/seeded — a genuine trade-off (it cannot claim to describe real deployed-agent behavior) but one documented candidly in its own README/methodology rather than obscured, including an honestly-reported *negative* result (near-chance failure prediction from coarse features). No competing artifact reviewed here documents its limitations with comparable candor in the search snippets available; this is a positioning strength, not a "first ever" claim.

5. **No verified Kaggle-native multi-table relational offering.** The one directly comparable Kaggle artifact (`sunil123kumar/ai-agent-failure-benchmark-dataset`, ~1,500 samples) appears to be single-table and its full schema could not be verified in this research pass — an open item to manually confirm before making any comparative claim in a public dataset card. Do not claim definitive superiority over it without opening the actual Kaggle page and reading its columns directly.

**Bottom line for the dataset card / write-up:** position this dataset as filling a structural gap (relational, taxonomy-linked, recovery-modeled, Kaggle-native, fully reproducible) rather than a novelty gap (being first to study agent failure) — the research area is active and crowded at the paper level, but the specific combination of features here was not found duplicated in any single artifact during this search.

---

## Our Differentiation (v2)

Reviewed against the projects above after the v2 upgrade (multi-failure
cascading trajectories, feature-driven failure probability, repeated
recovery attempts, evidence-based grounding). This section is an update to
the "What's missing" analysis above, evaluated specifically against v2's
actual capabilities — not a re-run of the original web research, which was
current as of 2026-08-27 and still stands for the landscape survey itself.

- **Relational structure.** Unchanged conclusion: no competitor found
  (TRAIL, AgentRx, ATBench, ToolFailBench, AgentErrorBench, the Kaggle
  `sunil123kumar` dataset) combines a full FK-linked chain across
  tasks/runs/steps/failures/recoveries/evaluations. v2 adds a tenth table
  (`evidence.csv`) and a self-referencing FK on `failure_events`
  (`parent_failure_id`) that none of the reviewed projects were found to
  have — AgentRx and ATBench both define failure taxonomies but neither
  was found to model *inter-failure causal relationships* as structured,
  queryable data (their papers discuss failure modes narratively, not via
  a resolvable graph).
- **Multi-failure trajectories.** TRAIL (148 traces, 841 unique errors)
  comes closest among the real-transcript projects — multiple errors do
  occur per trace — but TRAIL does not, per the available search results,
  expose an explicit per-trace failure count or a documented cascade
  relationship between errors within one trace the way v2's
  `failure_sequence`/`is_cascading`/`parent_failure_id` does.
- **Recovery as first-class, repeatable data.** "Failing Tools" (OpenReview
  j7YsSnA64D) is the closest conceptual match — injected runtime tool
  failures with detect/retry/fallback behaviors — but its size and schema
  were not available in this research pass. v2's `recovery_events` table
  goes further than a binary retry signal: it records
  `recovery_attempt_number` (so repeated attempts on the same failure are
  distinguishable data, not just narrative), and the notebooks measure
  that later attempts succeed less often — a finding, not an assumption.
  No reviewed competitor was found to expose this as structured per-attempt
  data.
- **Feature-driven, non-leaking failure prediction.** Not directly
  comparable to any reviewed project (none of AgentBench/WebArena/GAIA/
  ToolBench frame their task as "predict failure from pre-completion
  features" — they measure task success directly). This is a benchmark
  design choice specific to this dataset, not a claim of being first to
  study agent failure prediction generally; ML-focused agent-reliability
  papers likely exist outside what a search-snippet-based pass could
  surface.
- **Honesty about the direct Kaggle competitor.** `sunil123kumar/ai-agent-failure-benchmark-dataset`
  remains unverified in its full schema (JS-rendered page, not fetchable
  in this research pass). This document does not claim structural
  superiority over it beyond what was actually confirmed (~1,500 samples,
  apparently single-table from the snippet available) — that comparison
  should be finalized by manually opening the Kaggle page before any
  public claim is made.

**Bottom line, updated for v2:** the structural gap identified in the
original research (relational depth, recovery as first-class data,
taxonomy-to-data traceability) is, if anything, wider after the v2
upgrade — cascades and repeated-attempt recovery add structure not found
in any single reviewed competitor. This remains a structural
differentiation claim, not a "first ever" claim, and the one open
verification item (the Kaggle competitor's actual schema) should be
resolved before publishing any comparative statement.

## Search log

Queries actually run via WebSearch on 2026-08-27:

1. `Kaggle "Agent Arena" dataset`
2. `Kaggle "AI Agent Security" competition`
3. `"AgentRx" AI agent`
4. `"ATBench" benchmark`
5. `Google FACTS grounding benchmark`
6. `"AgentEval" benchmark framework`
7. `"agent trajectory dataset" kaggle`
8. `"LLM agent failure" benchmark taxonomy 2025 2026`
9. `"tool use failure" dataset LLM agents`
10. `agent evaluation benchmark 2026 multi-step reasoning`
11. `AgentBench LLM agents benchmark GitHub`
12. `ToolBench LLM tool learning dataset`
13. `"AgentOps" benchmark observability agent monitoring`
14. `WebArena benchmark web agents realistic environments`
15. `SWE-bench agent trajectories dataset`
16. `RAG agent evaluation benchmark hallucination grounding 2025 2026`
17. `agent self-correction recovery benchmark dataset`
18. `kaggle.com/datasets "agent" "failure" OR "trajectory" OR "tool use"`
19. `"ai-agent-failure-benchmark-dataset" kaggle sunil123kumar`
20. `TRAIL Trace Reasoning Agentic Issue Localization dataset`
21. `Kaggle "agent evaluation" OR "agent benchmark" dataset 2026 synthetic`
22. `GAIA benchmark general AI assistants agent`
23. `"AgentAtlas" LLM agents benchmark arxiv 2605.20530`
24. `Holistic Agent Leaderboard HAL agent evaluation infrastructure`
25. `"AI Agent Security - Multi-Step Tool Attacks" kaggle organizer prize dataset size`

One direct page fetch was attempted (`kaggle.com/datasets/sunil123kumar/ai-agent-failure-benchmark-dataset`) via WebFetch; it returned only the page title, not the full dataset description — Kaggle dataset pages are JS-rendered and not reliably scrapable this way. This is flagged inline above wherever that dataset's details are unverified.
