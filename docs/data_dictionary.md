# Data Dictionary — Agent Failure Atlas 2026 (v2)

Every field in every published table is documented below. No undocumented
columns exist in the shipped CSVs.

**v2 changes from v1:** `tasks.available_tools` added; `agents.capability_tier`
and `agents.execution_mode` added; `agent_runs.unique_tools_used` and
`agent_runs.available_tool_count` added, `failure_count` is now an
unbounded non-negative integer (was 0 or 1); `failure_events` gains
`failure_sequence`, `parent_failure_id`, `is_cascading`, `severity_level`;
`recovery_events` gains `recovery_attempt_number`; `evaluations.recovery_success`
(boolean) is replaced by `evaluations.recovery_success_rate` (float, since a
run can now have multiple failures with mixed outcomes) and gains
`cascading_failure_count`; a new `evidence.csv` table is added, and
`evaluations.grounding_score` is now computed from it rather than sampled.

---

## tasks.csv

One row = one unique task.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| task_id | string | No | Unique identifier for one task. | `task_00001` | primary key |
| task_domain | string | No | Domain category of the task. | one of 13 domains (see below) | — |
| task_type | string | No | Task type; currently mirrors `task_domain`. | same as task_domain | — |
| difficulty | string | No | Documented difficulty tier. Drives failure-probability modulation — see `docs/methodology.md`. | `easy`, `medium`, `hard` | — |
| task_description | string | No | Self-contained natural-language task statement, understandable without hidden context. | `Research quarterly revenue trends using web search and summarize the top 3 findings with sources.` | — |
| constraints | string | No | Explicit constraints the agent must satisfy, semicolon-separated. | `Must use only tools from the web_research toolset; Must return exactly 3 items` | — |
| required_capabilities | string | No | Human-readable capability requirement. | `web research` | — |
| expected_tools | string | No | Comma-separated tool names expected to be relevant (the domain's base toolset). | `web_search,browser,validator` | tools.tool_name (each) |
| available_tools | string | **v2** | No | Comma-separated tool names actually available for this task — `expected_tools` plus, on ~50% of tasks, one extra domain-adjacent tool. Drives `available_tool_count` and the tool-selection failure-probability nudge; a genuine pre-completion predictive feature. | `web_search,browser,validator,api_client` | tools.tool_name (each) |
| ground_truth | string | No | Identifier/reference for the task's correct-answer artifact (synthetic placeholder key in this release; see Limitations). | `gt_web_research_quarterly_revenue_trends_3items` | — |
| success_criteria | string | No | Machine/evaluator-checkable statement of what a correct final answer must satisfy. | `Final answer must contain exactly 3 items, each traceable to a tool observation, and satisfy all stated constraints.` | — |

**Domains:** web_research, document_analysis, data_analysis, coding, api_workflows, planning, information_retrieval, structured_extraction, multi_step_reasoning, file_operations, constraint_satisfaction, rag, verification.

---

## agents.csv

One row = one agent configuration.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| agent_id | string | No | Unique identifier for one agent configuration. | `agent_03` | primary key |
| model | string | No | Simulated model identifier. | `claude-sonnet-cls` | — |
| model_family | string | No | Model family grouping. | `claude`, `gpt-4.1`, `llama`, `mixtral` | — |
| provider | string | No | Simulated provider label. | `sim-anthropic` | — |
| framework | string | No | Agent orchestration framework. | `react-loop`, `function-call`, `plan-execute` | — |
| configuration | string | No | Named configuration variant distinguishing agents that share a model. | `default`, `cautious`, `fast`, `planner` | — |
| temperature | float | No | Sampling temperature used by this configuration. | `0.0`-`0.4` | — |
| tool_policy | string | No | Tool-invocation policy. | `auto`, `required` | — |
| capability_tier | string | **v2** | No | Simulated capability tier — a labeled generation parameter that modulates failure/recovery probability (see `docs/methodology.md`). **Not a claim about any real model's actual capability.** | `high`, `medium`, `low` | — |
| execution_mode | string | **v2** | No | Explicitly labels every row as simulated, distinguishing this from a table that could contain real model execution. | `synthetic_simulation` (constant in this release) | — |

Model, configuration, and framework are tracked as distinct fields — two rows sharing a `model` value are different **agent configurations**, not different models.

---

## tools.csv

One row = one tool in the catalogue.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| tool_name | string | No | Unique tool identifier. | `web_search` | primary key |
| tool_category | string | No | Category of the tool. | `search`, `retrieval`, `database`, `calculator`, `code_execution`, `file_operation`, `API`, `browser`, `validation` | — |
| description | string | No | One-line description of what the tool does. | `Full-text search over a simulated web index.` | — |
| input_schema | string | No | Informal schema of the tool's input. | `{query: string, top_k: int}` | — |
| output_schema | string | No | Informal schema of the tool's output. | `{results: [{title, snippet, url}]}` | — |
| risk_level | string | No | Qualitative risk of the tool's side effects. | `low`, `medium`, `high` | — |

---

## taxonomy.csv

One row = one machine-readable failure-taxonomy entry.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| taxonomy_id | string | No | Unique identifier. | `TAX-001` | primary key |
| level_1 | string | No | Top-level failure category. | `planning`, `tool_use`, `retrieval`, `reasoning`, `state`, `verification`, `execution`, `output` | — |
| level_2 | string | No | Specific failure type within the category. | e.g. `wrong_tool` | referenced by failure_events.failure_type |
| definition | string | No | Precise definition of this failure type. | see docs/taxonomy.md | — |
| example | string | No | Concrete example illustrating the failure. | see docs/taxonomy.md | — |
| severity_guidance | string | No | Typical severity band for this failure type, per the documented numeric rubric in docs/taxonomy.md. | `low` … `critical` | — |
| recoverable_typically | bool | No | Whether this failure type is typically recoverable. Every `severity_guidance=critical` (rubric level 4) type is `False` by construction — see docs/taxonomy.md "Severity rubric." | `True`/`False` | — |

Cascade edges (which failure types can directly cause which others) are documented per-type in `docs/taxonomy.md` and encoded in `src/generation/taxonomy.py::FAILURE_CASCADES`; they are not a column of this table because they form a graph, not a per-row scalar — see `failure_events.parent_failure_id` for the per-occurrence realization.

---

## agent_runs.csv

One row = one complete execution of one agent on one task.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| run_id | string | No | Unique identifier for one complete agent execution. | `run_000184` | primary key |
| task_id | string | No | Task this run executed. | `task_00042` | tasks.task_id |
| agent_id | string | No | Agent configuration used. | `agent_03` | agents.agent_id |
| run_number | int | No | 1-indexed run number among the runs generated for this task. | `1`, `2`, `3` | — |
| start_time | string (ISO 8601) | No | Synthetic run start timestamp. | `2026-06-01T00:03:10+00:00` | — |
| end_time | string (ISO 8601) | No | Synthetic run end timestamp, `start_time + latency_ms`. | — | — |
| latency_ms | int | No | Total run latency in milliseconds (includes all recovery attempts' latency). **Post-completion** — see the leakage note in `notebooks/02_predict_agent_failure.ipynb` before using this as a predictive feature. | `>= 0` | — |
| input_tokens | int | No | Total simulated input tokens consumed. | `>= 0` | — |
| output_tokens | int | No | Total simulated output tokens produced (includes all recovery attempts' token cost). | `>= 0` | — |
| total_tokens | int | No | `input_tokens + output_tokens`. | `>= 0` | — |
| tool_call_count | int | No | Number of steps in this run with a non-null `tool_name` (includes recovery-injected steps). **Post-completion** — inflated by failures; not a safe predictive feature (see `notebooks/02_predict_agent_failure.ipynb`). | `>= 0` | — |
| unique_tools_used | int | **v2** | No | Count of distinct tools called across the whole run. | `>= 0`, `<= tool_call_count` | — |
| available_tool_count | int | **v2** | No | Number of tools available for this run's task (denormalized from `tasks.available_tools`). A genuine pre-completion feature. | `>= 3` | — |
| failure_count | int | No | Number of failure_events rows for this run. **v2: unbounded** (was 0 or 1 in v1); capped at `MAX_FAILURES_PER_RUN=4` by generator safety limit, not by schema. | `>= 0` | — |
| final_status | string | No | Final outcome of the run. `partial_success` means at least one failure was diagnosed and not every failure was successfully recovered, but no *critical* failure went unrecovered. | `success`, `partial_success`, `failed` | — |
| final_answer | string | No | Short synthetic summary of the run's final answer. | `Completed web_research task with 4 tool calls.` | — |

---

## trajectory_steps.csv

One row = one observable execution step. This is the most important table — it reconstructs the full execution.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| run_id | string | No | Run this step belongs to. | `run_000184` | agent_runs.run_id |
| step_id | string | No | Unique step identifier. | `run_000184_s003` | primary key |
| sequence_number | int | No | 1-indexed position of this step within its run; strictly increasing per run. | `1, 2, 3, …` | — |
| action_type | string | No | Type of action taken at this step. | `plan`, `tool_call`, `observe`, `verify`, `correct`, `finalize` | — |
| tool_name | string | Yes | Tool invoked at this step, if any. | `web_search` or empty | tools.tool_name |
| tool_input | string | Yes | Structured (informal-JSON) representation of the tool call input, with randomized arguments/modifiers per call (v2: no longer a fixed per-domain template). | `{query: 'document analysis top-N', top_k: 7}` | — |
| tool_output | string | Yes | Structured (informal-JSON) representation of the tool call output, with randomized result sizes and, on ~12% of tool-bearing steps, near-miss noise (timeout, partial response, malformed response, etc.) independent of whether the run ends up with a diagnosed failure — see `docs/methodology.md` "Leakage avoidance." | `{results: 7 items, avg_relevance: 0.82}` | — |
| observation | string | No | Short, concise natural-language description of what happened at this step. **Not** a chain-of-thought / hidden-reasoning trace — see docs/data_governance.md. Never contains failure-indicating language while `step_status='ok'` — validated automatically (see `docs/methodology.md` "Leakage avoidance"). | `Step 3 (execution): 'sql_query' returned a typical result set.` | — |
| decision_category | string | No | Category of agent decision at this step. | `planning`, `retrieval`, `tool_selection`, `execution`, `verification`, `correction`, `finalization` | — |
| step_status | string | No | Outcome status of this step. | `ok`, `error`, `recovered`, `failed` | — |

---

## failure_events.csv

One row = one diagnosed failure event. **v2: a run can have zero, one, or several** (see `docs/methodology.md`).

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| failure_id | string | No | Unique identifier. | `run_000184_f01` | primary key |
| run_id | string | No | Run this failure occurred in. | `run_000184` | agent_runs.run_id |
| step_id | string | No | Step at which the failure was diagnosed. | `run_000184_s003` | trajectory_steps.step_id |
| failure_sequence | int | **v2** | No | 1-indexed position of this failure among all failures in its run; forms a contiguous `1..N` per run. | `1, 2, 3, …` | — |
| parent_failure_id | string | **v2** | Yes | The failure that directly caused this one, if this failure is a documented cascade (`is_cascading=True`); null otherwise. | `run_000184_f01` or empty | failure_events.failure_id |
| is_cascading | bool | **v2** | No | Whether this failure's type is a documented cascade target of its `parent_failure_id`'s failure type (see `docs/taxonomy.md` "Failure cascades"). | `True`/`False` | — |
| failure_type | string | No | Specific failure type (taxonomy level_2). | e.g. `wrong_tool` | taxonomy.level_2 |
| failure_category | string | No | Failure category (taxonomy level_1). | e.g. `tool_use` | taxonomy.level_1 |
| severity | string | No | Severity of this specific occurrence (text band). | `low` … `critical` | — |
| severity_level | int | **v2** | No | Numeric severity per the documented rubric in `docs/taxonomy.md` (1=minor, 2=moderate, 3=major, 4=critical). | `1`-`4` | — |
| is_critical | bool | No | Whether this failure is treated as critical (`severity_level` 3 or 4 / severity `high` or `critical`). | `True`/`False` | — |
| failure_trigger | string | No | What triggered/where the failure was detected; notes the cascade source when applicable. | `execution at step 3 in decision category 'execution'; cascaded from run_000184_f01` | — |
| failure_description | string | No | Definition of the failure type (from the taxonomy). | — | — |
| recoverable | bool | No | Whether this failure type is typically recoverable, per taxonomy. `False` for every `severity_level=4` type by construction. | `True`/`False` | — |

---

## recovery_events.csv

One row = one recovery **attempt** (or one non-attempt row) for one failure. **v2: a single failure can have multiple recovery_events rows** (repeated attempts with different strategies).

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| recovery_id | string | No | Unique identifier. | `run_000184_f01_r02` | primary key |
| failure_id | string | No | Failure this recovery responds to. | `run_000184_f01` | failure_events.failure_id |
| run_id | string | No | Run this recovery occurred in. | `run_000184` | agent_runs.run_id |
| recovery_attempt_number | int | **v2** | No | 1-indexed attempt number for this failure (`0` means recovery was never attempted — exactly one such row exists per un-attempted failure). Attempt numbers for an attempted failure form a contiguous `1..N`. | `0`, `1`, `2` | — |
| recovery_attempted | bool | No | Whether the agent attempted recovery at all. | `True`/`False` | — |
| recovery_strategy | string | Yes | Strategy used, if attempted. | `retry`, `alternative_tool`, `reformulate_query`, `verify_result`, `rollback`, `replan`, `ask_for_clarification`, `use_additional_evidence`, `change_execution_strategy` | — |
| recovery_trigger | string | Yes | What triggered this recovery attempt. | `step_status=error at run_000184_s003` (attempt 1) or `prior recovery attempt 1 failed` (attempt 2+) | — |
| recovery_steps | int | No | Number of extra steps inserted into the trajectory for this attempt. | `0` if not attempted, else `1`-`3` | — |
| recovery_success | bool | No | Whether this specific attempt succeeded. Later attempts on the same failure succeed less often (a documented, measured effect — see `notebooks/03_recovery_analysis.ipynb`). | `True`/`False` | — |
| recovery_latency_ms | int | No | Additional latency incurred by this attempt. | `>= 0` | — |
| recovery_token_cost | int | No | Additional tokens consumed by this attempt. | `>= 0` | — |
| final_outcome | string | No | Outcome of the run following this specific attempt. | `success`, `partial_success`, `failed` | — |

---

## evidence.csv

One row = one claim/evidence relationship for a run. **New in v2.** Introduced so `grounding_score` is a genuinely computed metric rather than a sampled proxy — see `docs/methodology.md`.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| evidence_id | string | No | Unique identifier. | `run_000184_ev03` | primary key |
| run_id | string | No | Run this evidence/claim belongs to. | `run_000184` | agent_runs.run_id |
| task_id | string | No | Task this run executed (denormalized). | `task_00042` | tasks.task_id |
| source_type | string | No | Kind of source the claim is checked against. | `retrieved_document`, `tool_output`, `api_response` | — |
| claim | string | No | The claim being evaluated for groundedness. | `Claim 2 derived from document_analysis trajectory for run_000184.` | — |
| relevance | float | No | How relevant the cited source is to the claim. | `[0.5, 1.0]` | — |
| supports_claim | bool | No | Whether the source supports the claim. `evaluations.grounding_score` for this run = mean of this column across its evidence rows. | `True`/`False` | — |
| contradicts_claim | bool | No | Whether the source actively contradicts the claim (more likely when the run had conflicting retrieved information). | `True`/`False` | — |

---

## evaluations.csv

One row = one run's evaluation. Every metric's computation is documented in `docs/methodology.md`; no metric here is a black box.

| field | type | nullable | description | allowed values / example | relationship |
|---|---|---|---|---|---|
| run_id | string | No | Run being evaluated. | `run_000184` | agent_runs.run_id (1:1) |
| task_success | bool | No | Whether `final_status` is `success` or `partial_success`. | `True`/`False` | — |
| constraint_satisfaction | float | No | `1.0` if `final_status == success`, `0.5` if `partial_success`, `0.0` if `failed`. | `[0, 1]` | — |
| failure_count | int | No | Same as agent_runs.failure_count (denormalized for convenience). **v2: unbounded**, was 0/1. | `>= 0` | — |
| critical_failure_count | int | No | Count of this run's failures with `is_critical == True`. **v2: unbounded**, was 0/1. | `>= 0` | — |
| cascading_failure_count | int | **v2** | No | Count of this run's failures with `is_cascading == True`. | `>= 0` | — |
| recovery_success_rate | float | **v2 (replaces v1's boolean `recovery_success`)** | Yes | Fraction of this run's failures that were successfully recovered (`len(recovered failure_ids) / failure_count`); null if `failure_count == 0`. Replaces v1's single boolean because a run can now have several failures with mixed recovery outcomes. | `[0, 1]` or null | — |
| tool_efficiency | float | No | `min(1.0, expected_tool_count / actual_tool_calls)`; see methodology.md. | `[0, 1]` | — |
| trajectory_efficiency | float | No | `min(1.0, reference_length / actual_length)`, reference length set per difficulty tier; see methodology.md. | `[0, 1]` | — |
| grounding_score | float | **v2: now computed, not sampled** | No | Mean of `evidence.supports_claim` across this run's evidence rows — a genuinely computed groundedness signal, not a distribution sampled conditional on outcome (v1 behavior). See methodology.md. | `[0, 1]` | evidence.run_id (aggregated) |
| final_answer_score | float | No | `1.0` success / `0.5` partial / `0.0` failed. | `[0, 1]` | — |
| reliability_score | float | No | Weighted composite: `0.5*task_success + 0.2*(1 - has_critical_failure) + 0.2*(recovery_success_rate or 1 if no failure) + 0.1*tool_efficiency`. | `[0, 1]` | — |
