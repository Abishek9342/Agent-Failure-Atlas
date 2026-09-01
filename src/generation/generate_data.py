"""Synthetic generator for Agent Failure Atlas 2026 (v2).

Simulates the full lifecycle of a multi-step AI-agent execution:
Task -> Agent -> trajectory of steps -> zero or more (possibly cascading)
failures, each with its own recovery attempt -> final outcome ->
evaluation, grounded against an explicit evidence table. All ten tables
are produced from one seeded run so foreign keys are correct by
construction and never need post-hoc repair.

This is a SIMULATION, not a replay of real model transcripts: step content
(tool inputs/outputs, observations) is templated with randomized arguments,
result sizes, and occasional noise (partial results, conflicting
information, malformed responses) from the task/tool/failure context,
rather than sampled from live model calls. That keeps the dataset
reproducible without proprietary API dependencies (see docs/reproducibility.md)
while still encoding a realistic, internally-consistent causal structure.

v2 changes from v1 (see docs/methodology.md "v2 upgrade" section for the
full rationale):
  - Multiple, possibly cascading, failures per trajectory (previously: at
    most one).
  - Failure probability is influenced by task difficulty, tool count,
    trajectory length-so-far, and retrieval-conflict state — not sampled
    independently of observable features (previously: uniform probability
    largely unlinked to features, which produced a near-chance failure
    prediction benchmark).
  - Trajectory step content (tool arguments, result sizes, partial/
    malformed/conflicting outputs) is randomized per call, not just per
    domain, and pre-failure step text never leaks the failure label.
  - grounding_score is computed from an explicit evidence.csv table of
    claim/source/supported relationships, not sampled from a distribution
    conditioned on the outcome.

Deterministic: same --seed always produces the same files.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from taxonomy import (  # noqa: E402
    ACTION_TYPES, DECISION_CATEGORIES, FAILURE_TAXONOMY, RECOVERY_STRATEGIES,
    all_failure_types, cascade_targets, failure_category_of, iter_taxonomy_rows,
    severity_level,
)

# ---------------------------------------------------------------------------
# Reference data: agents, tools, task domains
# ---------------------------------------------------------------------------

AGENTS = [
    # agent_id, model, model_family, provider, framework, configuration, temperature, tool_policy, capability_tier, execution_mode
    ("agent_01", "gpt-4.1-class-a",   "gpt-4.1",  "sim-openai",    "react-loop",   "default",  0.2, "auto",     "high",   "synthetic_simulation"),
    ("agent_02", "gpt-4.1-class-a",   "gpt-4.1",  "sim-openai",    "react-loop",   "cautious", 0.0, "auto",     "high",   "synthetic_simulation"),
    ("agent_03", "claude-sonnet-cls", "claude",   "sim-anthropic", "react-loop",   "default",  0.2, "auto",     "high",   "synthetic_simulation"),
    ("agent_04", "claude-haiku-cls",  "claude",   "sim-anthropic", "react-loop",   "default",  0.2, "auto",     "medium", "synthetic_simulation"),
    ("agent_05", "llama-70b-class",   "llama",    "sim-meta",      "function-call","default",  0.3, "auto",     "medium", "synthetic_simulation"),
    ("agent_06", "gpt-4.1-mini-cls",  "gpt-4.1",  "sim-openai",    "function-call","fast",     0.4, "required", "low",    "synthetic_simulation"),
    ("agent_07", "claude-sonnet-cls", "claude",   "sim-anthropic", "plan-execute", "planner",  0.2, "auto",     "high",   "synthetic_simulation"),
    ("agent_08", "mixtral-8x7b-cls",  "mixtral",  "sim-mistral",   "react-loop",   "default",  0.3, "auto",     "low",    "synthetic_simulation"),
    ("agent_09", "gpt-4.1-class-a",   "gpt-4.1",  "sim-openai",    "plan-execute", "planner",  0.1, "auto",     "high",   "synthetic_simulation"),
    ("agent_10", "llama-8b-class",    "llama",    "sim-meta",      "function-call","fast",     0.4, "required", "low",    "synthetic_simulation"),
]
# capability_tier drives failure-probability modulation below: higher-tier
# (larger/stronger) simulated agents get a lower base failure rate, lower-tier
# agents get a higher one. This is a *labeled simulation parameter*, not a
# claim about real model performance -- see docs/data_governance.md.
CAPABILITY_FAILURE_MULTIPLIER = {"high": 0.80, "medium": 1.0, "low": 1.30}

TOOLS = [
    # tool_name, tool_category, description, input_schema, output_schema, risk_level
    ("web_search", "search", "Full-text search over a simulated web index.", "{query: string, top_k: int}", "{results: [{title, snippet, url}]}", "low"),
    ("doc_retriever", "retrieval", "Dense retrieval over a fixed document corpus.", "{query: string, top_k: int}", "{chunks: [{doc_id, text, score}]}", "low"),
    ("sql_query", "database", "Read-only query against a tabular data store.", "{sql: string}", "{rows: [object], row_count: int}", "medium"),
    ("calculator", "calculator", "Evaluates a numeric expression.", "{expression: string}", "{value: number}", "low"),
    ("code_executor", "code_execution", "Runs a short Python snippet in a sandbox.", "{code: string}", "{stdout: string, stderr: string, exit_code: int}", "medium"),
    ("file_reader", "file_operation", "Reads the contents of a named file.", "{path: string}", "{content: string}", "low"),
    ("file_writer", "file_operation", "Writes content to a named file.", "{path: string, content: string}", "{success: bool}", "high"),
    ("api_client", "API", "Calls a named external REST API endpoint.", "{endpoint: string, params: object}", "{status: int, body: object}", "medium"),
    ("browser", "browser", "Navigates to a URL and extracts visible text.", "{url: string}", "{text: string}", "medium"),
    ("validator", "validation", "Checks a value against a declared constraint set.", "{value: object, constraints: object}", "{valid: bool, violations: [string]}", "low"),
]

DOMAINS = [
    "web_research", "document_analysis", "data_analysis", "coding",
    "api_workflows", "planning", "information_retrieval",
    "structured_extraction", "multi_step_reasoning", "file_operations",
    "constraint_satisfaction", "rag", "verification",
]

DOMAIN_TOOLS = {
    "web_research": ["web_search", "browser", "validator"],
    "document_analysis": ["doc_retriever", "file_reader", "validator"],
    "data_analysis": ["sql_query", "calculator", "code_executor"],
    "coding": ["code_executor", "file_reader", "file_writer"],
    "api_workflows": ["api_client", "validator", "calculator"],
    "planning": ["doc_retriever", "calculator", "validator"],
    "information_retrieval": ["web_search", "doc_retriever", "validator"],
    "structured_extraction": ["file_reader", "doc_retriever", "validator"],
    "multi_step_reasoning": ["calculator", "sql_query", "validator"],
    "file_operations": ["file_reader", "file_writer", "validator"],
    "constraint_satisfaction": ["validator", "calculator", "sql_query"],
    "rag": ["doc_retriever", "web_search", "validator"],
    "verification": ["validator", "sql_query", "calculator"],
}
# Some domains additionally have a 4th "extra" tool available at random,
# giving genuine variation in available_tool_count (a predictive feature).
DOMAIN_EXTRA_TOOL = {
    "web_research": "api_client", "document_analysis": "sql_query",
    "data_analysis": "api_client", "coding": "sql_query",
    "api_workflows": "browser", "planning": "web_search",
    "information_retrieval": "file_reader", "structured_extraction": "sql_query",
    "multi_step_reasoning": "code_executor", "file_operations": "code_executor",
    "constraint_satisfaction": "code_executor", "rag": "file_reader",
    "verification": "web_search",
}

DIFFICULTIES = ["easy", "medium", "hard"]
DIFFICULTY_WEIGHTS = [0.35, 0.40, 0.25]
DIFFICULTY_ORDINAL = {"easy": 0, "medium": 1, "hard": 2}

TASK_TEMPLATES = {
    "web_research": "Research {topic} using web search and summarize the top {n} findings with sources.",
    "document_analysis": "Read the provided document set on {topic} and extract the {n} key claims with citations.",
    "data_analysis": "Query the {topic} table and compute the requested aggregate for the last {n} periods.",
    "coding": "Write and run a script that solves {topic} and returns the result for {n} test cases.",
    "api_workflows": "Call the {topic} API and assemble a report combining {n} endpoint responses.",
    "planning": "Produce a {n}-step plan to accomplish {topic} respecting the stated constraints.",
    "information_retrieval": "Find the {n} most relevant sources for {topic} and rank them by relevance.",
    "structured_extraction": "Extract {n} structured fields describing {topic} from the source file.",
    "multi_step_reasoning": "Answer a multi-step question about {topic} requiring {n} intermediate computations.",
    "file_operations": "Read {topic}, transform it, and write {n} output files with the results.",
    "constraint_satisfaction": "Find an assignment for {topic} satisfying all {n} stated constraints.",
    "rag": "Answer the question about {topic} grounded only in the retrieved {n} passages.",
    "verification": "Verify the {n} claims about {topic} against the source data and flag unsupported ones.",
}

TOPICS = [
    "quarterly revenue trends", "customer churn drivers", "vendor contract terms",
    "shipping delay root causes", "employee onboarding steps", "inventory reorder points",
    "regional sales performance", "product defect reports", "compliance audit findings",
    "marketing campaign ROI", "supply chain bottlenecks", "support ticket backlog",
    "pricing tier comparison", "server incident timeline", "budget variance analysis",
    "hiring pipeline metrics", "warehouse capacity planning", "subscription renewal rates",
    "competitor feature matrix", "energy usage patterns",
]

FAILURE_TYPES = all_failure_types()

# Which failure categories are plausible at which decision category (keeps causal structure realistic)
CATEGORY_BY_DECISION = {
    "planning": ["planning"],
    "retrieval": ["retrieval", "tool_use"],
    "tool_selection": ["tool_use"],
    "execution": ["execution", "tool_use", "state"],
    "verification": ["verification", "reasoning"],
    "correction": ["reasoning", "state"],
    "finalization": ["output"],
}

RECOVERY_APPLICABILITY = {
    "planning": ["replan", "ask_for_clarification", "change_execution_strategy"],
    "tool_use": ["alternative_tool", "retry", "change_execution_strategy"],
    "retrieval": ["reformulate_query", "use_additional_evidence", "alternative_tool"],
    "reasoning": ["verify_result", "use_additional_evidence", "replan"],
    "state": ["rollback", "replan", "verify_result"],
    "verification": ["verify_result", "use_additional_evidence"],
    "execution": ["retry", "rollback", "alternative_tool"],
    "output": ["verify_result", "replan", "ask_for_clarification"],
}

UNRECOVERABLE_TYPES = {l2 for l1, l2, definition, example, severity, recoverable in iter_taxonomy_rows() if not recoverable}
MAX_FAILURES_PER_RUN = 4  # hard safety cap; realistic runs rarely approach it

# --- randomized template vocabularies (trajectory realism, v2) -------------
QUERY_MODIFIERS = ["last quarter", "region-filtered", "top-N", "raw", "normalized",
                    "deduplicated", "time-windowed", "cross-referenced"]
RESULT_SIZE_WORDS = {"empty": 0, "sparse": 1, "small": 3, "typical": 7, "large": 22}
ERROR_KINDS = ["timeout", "rate_limited", "malformed_response", "partial_response",
               "schema_mismatch", "stale_cache_hit"]


def build_reference_tables():
    agents_df = pd.DataFrame(AGENTS, columns=[
        "agent_id", "model", "model_family", "provider", "framework",
        "configuration", "temperature", "tool_policy", "capability_tier", "execution_mode",
    ])
    tools_df = pd.DataFrame(TOOLS, columns=[
        "tool_name", "tool_category", "description", "input_schema", "output_schema", "risk_level",
    ])
    taxonomy_rows = []
    for i, (l1, l2, definition, example, severity, recoverable) in enumerate(iter_taxonomy_rows(), start=1):
        taxonomy_rows.append({
            "taxonomy_id": f"TAX-{i:03d}", "level_1": l1, "level_2": l2,
            "definition": definition, "example": example,
            "severity_guidance": severity, "recoverable_typically": recoverable,
        })
    taxonomy_df = pd.DataFrame(taxonomy_rows)
    return agents_df, tools_df, taxonomy_df


def make_tasks(rng: np.random.Generator, n_tasks: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n_tasks + 1):
        domain = rng.choice(DOMAINS)
        difficulty = rng.choice(DIFFICULTIES, p=DIFFICULTY_WEIGHTS)
        topic = rng.choice(TOPICS)
        n = int(rng.integers(2, 6))
        desc = TASK_TEMPLATES[domain].format(topic=topic, n=n)
        n_constraints = {"easy": 1, "medium": 2, "hard": 3}[difficulty]
        constraints = "; ".join([
            f"Must use only tools from the {domain} toolset",
            f"Must return exactly {n} items" if n_constraints > 1 else None,
            "Must cite the source of every factual claim" if n_constraints > 2 else None,
        ][:n_constraints]) if n_constraints else "None"
        base_tools = DOMAIN_TOOLS[domain]
        has_extra_tool = bool(rng.random() < 0.5)
        available_tools = base_tools + ([DOMAIN_EXTRA_TOOL[domain]] if has_extra_tool else [])
        rows.append({
            "task_id": f"task_{i:05d}",
            "task_domain": domain,
            "task_type": domain,
            "difficulty": difficulty,
            "task_description": desc,
            "constraints": constraints,
            "required_capabilities": domain.replace("_", " "),
            "expected_tools": ",".join(base_tools),
            "available_tools": ",".join(available_tools),
            "ground_truth": f"gt_{domain}_{topic.replace(' ', '_')}_{n}items",
            "success_criteria": f"Final answer must contain exactly {n} items, each traceable to a tool observation, and satisfy all stated constraints.",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Trajectory content realism helpers
# ---------------------------------------------------------------------------

def render_tool_input(rng, tool_name, domain, topic_hint, step_no):
    modifier = rng.choice(QUERY_MODIFIERS)
    if tool_name in ("web_search", "doc_retriever", "browser"):
        top_k = int(rng.integers(3, 12))
        return f"{{query: '{topic_hint} {modifier}', top_k: {top_k}}}"
    if tool_name == "sql_query":
        cols = int(rng.integers(2, 6))
        return f"{{sql: 'SELECT * FROM {domain}_{modifier.replace(' ', '_')} LIMIT {cols*10}'}}"
    if tool_name == "calculator":
        return f"{{expression: '({int(rng.integers(1,999))} * {round(float(rng.uniform(0.1,9.9)),2)}) / {int(rng.integers(1,50))}'}}"
    if tool_name == "code_executor":
        return f"{{code: 'run_{domain}_step_{step_no}({modifier!r})'}}"
    if tool_name == "file_reader":
        return f"{{path: '/data/{domain}/{modifier.replace(' ', '_')}.csv'}}"
    if tool_name == "file_writer":
        return f"{{path: '/out/{domain}_result_{step_no}.json', content: '<{modifier}_payload>'}}"
    if tool_name == "api_client":
        return f"{{endpoint: '/v1/{domain}/{modifier.replace(' ', '_')}', params: {{page: {int(rng.integers(1,5))}}}}}"
    if tool_name == "validator":
        return f"{{value: '<step_{step_no}_result>', constraints: '{modifier}'}}"
    return f"{{query: '{domain} step {step_no}'}}"


def render_tool_output(rng, tool_name, size_word, noisy_kind=None):
    """noisy_kind: None (clean) or one of ERROR_KINDS -- used ONLY for
    non-failure texture (near-miss noise that occurs on both failing and
    non-failing steps) to avoid leaking the failure label into text. Actual
    diagnosed failures overwrite this with explicit failure text separately.
    """
    n = RESULT_SIZE_WORDS[size_word]
    if noisy_kind == "malformed_response":
        return "{result: '<truncated>', warning: 'response_size_exceeded_limit'}"
    if noisy_kind == "partial_response":
        return f"{{result: 'partial', items_returned: {max(n // 2, 0)}, items_expected: {n}}}"
    if noisy_kind == "timeout":
        return "{result: null, retry_after_ms: 1500}"
    if noisy_kind == "rate_limited":
        return "{result: null, status: 429}"
    if noisy_kind == "stale_cache_hit":
        return f"{{result: 'cached', age_seconds: {int(rng.integers(600, 9000))}, items: {n}}}"
    if noisy_kind == "schema_mismatch":
        return "{result: {unexpected_field: true}}"
    if tool_name in ("web_search", "doc_retriever", "browser"):
        return f"{{results: {n} items, avg_relevance: {round(float(rng.uniform(0.4, 0.98)), 2)}}}"
    if tool_name == "sql_query":
        return f"{{row_count: {n * 3}}}"
    if tool_name == "calculator":
        return f"{{value: {round(float(rng.uniform(-500, 5000)), 2)}}}"
    if tool_name == "code_executor":
        return f"{{stdout: '{n} lines', exit_code: 0}}"
    if tool_name == "file_reader":
        return f"{{content_length_kb: {n * 4}}}"
    if tool_name == "file_writer":
        return "{success: true}"
    if tool_name == "api_client":
        return f"{{status: 200, items: {n}}}"
    if tool_name == "validator":
        return f"{{valid: true, checked: {n}}}"
    return f"{{result: 'observation_ok', items: {n}}}"


def gen_trajectory(rng, run_id, task_row, difficulty_len):
    """Generate one trajectory's clean step skeleton (no failures yet)."""
    domain = task_row["task_domain"]
    available_tools = task_row["available_tools"].split(",")
    topic_hint = domain.replace("_", " ")
    n_steps = int(rng.integers(*difficulty_len[task_row["difficulty"]]))

    middle_len = max(n_steps - 2, 1)
    middle_categories = rng.choice(
        ["retrieval", "tool_selection", "execution", "correction"],
        size=middle_len, p=[0.30, 0.20, 0.40, 0.10],
    ).tolist()
    categories = ["planning"] + middle_categories + ["verification", "finalization"]

    steps = []
    for i, cat in enumerate(categories, start=1):
        if cat == "planning":
            action_type, tool_name = "plan", None
        elif cat == "finalization":
            action_type, tool_name = "finalize", None
        elif cat == "verification":
            action_type, tool_name = "verify", rng.choice(available_tools)
        elif cat == "correction":
            action_type, tool_name = "correct", rng.choice(available_tools)
        else:
            action_type, tool_name = "tool_call", rng.choice(available_tools)

        # texture noise independent of failure label: ~12% of tool-bearing
        # steps get a near-miss noisy-but-nonfatal output, regardless of
        # whether this run ends up with a diagnosed failure anywhere.
        noisy_kind = rng.choice(ERROR_KINDS) if (tool_name and rng.random() < 0.12) else None
        size_word = rng.choice(list(RESULT_SIZE_WORDS.keys()), p=[0.05, 0.15, 0.30, 0.35, 0.15])

        tool_input = render_tool_input(rng, tool_name, domain, topic_hint, i) if tool_name else None
        tool_output = render_tool_output(rng, tool_name, size_word, noisy_kind) if tool_name else None
        if tool_name and noisy_kind:
            observation = f"Step {i} ({cat}): tool '{tool_name}' returned a {noisy_kind.replace('_', ' ')}; continuing."
        elif tool_name:
            observation = f"Step {i} ({cat}): '{tool_name}' returned a {size_word} result set."
        else:
            observation = f"Step {i}: {cat} step."

        steps.append({
            "run_id": run_id,
            "step_id": f"{run_id}_s{i:03d}",
            "sequence_number": i,
            "action_type": action_type,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "observation": observation,
            "decision_category": cat,
            "step_status": "ok",
        })
    return steps


# ---------------------------------------------------------------------------
# Feature-driven, multi-failure, cascading injection
# ---------------------------------------------------------------------------

def step_failure_probability(base_prob, task_row, agent_row, available_tool_count,
                              steps_so_far, has_conflict_flag, prior_failure_count):
    """Per-step failure probability, modulated by observable pre-completion
    features. This is the core of the v2 predictive-signal upgrade: failure
    likelihood is now a function of difficulty, tool surface, trajectory
    depth, retrieval-conflict state, agent capability tier, and whether a
    prior failure already occurred in this run -- all of which are legitimate
    pre-completion features a predictor could use (see
    notebooks/02_predict_agent_failure.ipynb).
    """
    # Modulation is additive-in-log-odds-ish (small linear nudges), not fully
    # multiplicative, so effects compose gently instead of compounding into
    # near-certainty over a long trajectory. Each nudge alone is modest;
    # together they still produce a materially different failure rate across
    # difficulty/tool-count/agent-tier strata (see notebooks/02 feature
    # importances), which is the point -- but the base rate stays small
    # enough that a 10-20 step trajectory doesn't almost-surely trip.
    difficulty_nudge = 0.045 * DIFFICULTY_ORDINAL[task_row["difficulty"]]      # 0, +0.045, +0.09
    tool_nudge = 0.010 * max(available_tool_count - 3, 0)                      # +0.01 per extra tool beyond 3
    depth_nudge = 0.003 * min(steps_so_far, 20)                                # up to +0.06 by step 20
    conflict_nudge = 0.06 if has_conflict_flag else 0.0
    capability_nudge = {"high": -0.01, "medium": 0.0, "low": 0.025}[agent_row["capability_tier"]]
    prior_failure_nudge = 0.02 if prior_failure_count > 0 else 0.0             # a run already in trouble trips slightly more, but does not escalate further per additional failure

    p = base_prob + difficulty_nudge + tool_nudge + depth_nudge + conflict_nudge + capability_nudge + prior_failure_nudge
    return max(0.0, min(p, 0.85))


def pick_failure(rng, decision_category, parent_failure_type=None):
    """Pick a (category, type) pair -- either a cascade child of
    parent_failure_type (any taxonomy-documented downstream effect of the
    parent, per FAILURE_CASCADES -- cascades represent a causal narrative
    across the trajectory, not a same-step category match), or an
    independent draw constrained by CATEGORY_BY_DECISION as in v1."""
    if parent_failure_type is not None:
        candidates = cascade_targets(parent_failure_type)
        if candidates:
            ft = rng.choice(candidates)
            return failure_category_of(ft), ft, True
    plausible_categories = CATEGORY_BY_DECISION[decision_category]
    failure_category = rng.choice(plausible_categories)
    failure_type = rng.choice(list(FAILURE_TAXONOMY[failure_category].keys()))
    return failure_category, failure_type, False


def simulate_run(rng, run_id, task_row, agent_row, difficulty_len, failure_prob,
                  recovery_success_base_rate):
    """Full per-run simulation: trajectory + 0..N cascading failures each with
    its own recovery attempt. Returns (steps, failure_rows, recovery_rows,
    final_status)."""
    steps = gen_trajectory(rng, run_id, task_row, difficulty_len)
    available_tool_count = len(task_row["available_tools"].split(","))
    required_tool_count = len(task_row["expected_tools"].split(","))

    failure_rows, recovery_rows = [], []
    parent_failure_id = None
    parent_failure_type = None
    has_conflict_flag = bool(rng.random() < 0.18)  # task-level: were retrieved sources conflicting?
    run_failed_critically = False
    failure_ctr = 0

    # candidate step indices, in order, excluding the finalization step
    candidate_idxs = [i for i, s in enumerate(steps) if s["decision_category"] in CATEGORY_BY_DECISION]

    idx_cursor = 0
    while idx_cursor < len(candidate_idxs) and failure_ctr < MAX_FAILURES_PER_RUN and not run_failed_critically:
        i = candidate_idxs[idx_cursor]
        idx_cursor += 1
        step = steps[i]
        p = step_failure_probability(
            failure_prob, task_row, agent_row, available_tool_count,
            steps_so_far=i + 1, has_conflict_flag=has_conflict_flag,
            prior_failure_count=failure_ctr,
        )
        if rng.random() >= p:
            continue

        failure_category, failure_type, is_cascading = pick_failure(rng, step["decision_category"], parent_failure_type)
        definition, example, severity, recoverable_typically = FAILURE_TAXONOMY[failure_category][failure_type]
        is_critical = severity in ("high", "critical")
        failure_ctr += 1
        failure_id = f"{run_id}_f{failure_ctr:02d}"

        step["step_status"] = "error"
        step["observation"] = f"Failure detected: {failure_type} ({failure_category})."

        failure_row = {
            "failure_id": failure_id,
            "run_id": run_id,
            "step_id": step["step_id"],
            "failure_sequence": failure_ctr,
            "parent_failure_id": parent_failure_id if is_cascading else None,
            "is_cascading": bool(is_cascading),
            "failure_type": failure_type,
            "failure_category": failure_category,
            "severity": severity,
            "severity_level": severity_level(severity),
            "is_critical": bool(is_critical),
            "failure_trigger": f"{step['action_type']} at step {step['sequence_number']} in decision category '{step['decision_category']}'"
                                + (f"; cascaded from {parent_failure_id}" if is_cascading else ""),
            "failure_description": definition,
            "recoverable": bool(recoverable_typically),
        }
        failure_rows.append(failure_row)

        # --- recovery attempt(s) for this failure ---
        recovery_attempted = bool(recoverable_typically) and rng.random() < 0.85
        attempt_no = 0
        recovery_success = False
        if recovery_attempted:
            strategy_pool = RECOVERY_APPLICABILITY[failure_category]
            max_attempts = int(rng.integers(1, 3)) if not is_critical else 1
            insert_at = i + 1
            for attempt_no in range(1, max_attempts + 1):
                strategy = rng.choice(strategy_pool)
                success_rate = recovery_success_base_rate.get(strategy, 0.5)
                if is_critical:
                    success_rate *= 0.6
                success_rate *= (0.85 ** (attempt_no - 1))  # repeated attempts on the same failure get harder, not free
                recovery_success = bool(rng.random() < success_rate)

                n_recovery_steps = int(rng.integers(1, 4))
                recovery_latency_ms = int(rng.integers(400, 8000) * n_recovery_steps)
                recovery_token_cost = int(rng.integers(50, 600) * n_recovery_steps)

                for j in range(n_recovery_steps):
                    seq_frac = step["sequence_number"] + attempt_no * 0.1 + (j + 1) * 0.01
                    new_step = {
                        "run_id": run_id, "step_id": f"{run_id}_s{len(steps)+1:03d}r",
                        "sequence_number": seq_frac, "action_type": "correct",
                        "tool_name": step["tool_name"],
                        "tool_input": f"{{recovery_strategy: '{strategy}', attempt: {attempt_no}}}",
                        "tool_output": "{result: 'recovery_attempt'}",
                        "observation": f"Recovery attempt {attempt_no} (step {j + 1}/{n_recovery_steps}) using strategy '{strategy}'.",
                        "decision_category": "correction",
                        "step_status": "recovered" if (recovery_success and j == n_recovery_steps - 1) else "ok",
                    }
                    steps.insert(insert_at, new_step)
                    insert_at += 1

                recovery_rows.append({
                    "recovery_id": f"{failure_id}_r{attempt_no:02d}",
                    "failure_id": failure_id, "run_id": run_id,
                    "recovery_attempt_number": attempt_no,
                    "recovery_attempted": True, "recovery_strategy": strategy,
                    "recovery_trigger": f"step_status=error at {step['step_id']}" if attempt_no == 1 else f"prior recovery attempt {attempt_no - 1} failed",
                    "recovery_steps": n_recovery_steps, "recovery_success": recovery_success,
                    "recovery_latency_ms": recovery_latency_ms, "recovery_token_cost": recovery_token_cost,
                    "final_outcome": "success" if recovery_success else ("partial_success" if not is_critical else "failed"),
                })
                if recovery_success:
                    step["step_status"] = "recovered"
                    break
            if not recovery_success:
                # recovery itself can trigger a NEW failure (recovery causing another failure)
                if rng.random() < 0.28 and failure_ctr < MAX_FAILURES_PER_RUN:
                    parent_failure_id, parent_failure_type = failure_id, failure_type
                    continue
        else:
            recovery_rows.append({
                "recovery_id": f"{failure_id}_r01", "failure_id": failure_id, "run_id": run_id,
                "recovery_attempt_number": 0, "recovery_attempted": False, "recovery_strategy": None,
                "recovery_trigger": None, "recovery_steps": 0, "recovery_success": False,
                "recovery_latency_ms": 0, "recovery_token_cost": 0, "final_outcome": "failed",
            })

        if is_critical and not recovery_success:
            run_failed_critically = True
        elif not recovery_success:
            # non-critical, unresolved: may cascade into a downstream failure
            if rng.random() < 0.55:
                parent_failure_id, parent_failure_type = failure_id, failure_type
            else:
                parent_failure_id, parent_failure_type = None, None
        else:
            # even a successfully recovered failure occasionally leaves
            # residual risk that plausibly cascades (recovery is imperfect)
            if rng.random() < 0.10:
                parent_failure_id, parent_failure_type = failure_id, failure_type
            else:
                parent_failure_id, parent_failure_type = None, None

    # final status derivation
    if not failure_rows:
        final_status = "success"
    elif run_failed_critically:
        final_status = "failed"
    else:
        any_unresolved = any(
            not any(r["failure_id"] == f["failure_id"] and r["recovery_success"] for r in recovery_rows)
            for f in failure_rows
        )
        final_status = "partial_success" if any_unresolved else "success"

    # renumber sequence_number as clean ints, preserving order
    steps = sorted(steps, key=lambda s: s["sequence_number"])
    for k, s in enumerate(steps, start=1):
        s["sequence_number"] = k

    return steps, failure_rows, recovery_rows, final_status, has_conflict_flag


# ---------------------------------------------------------------------------
# Evidence table + grounding
# ---------------------------------------------------------------------------

def make_evidence_for_run(rng, run_id, task_row, has_conflict_flag, final_status):
    """Build a small set of claim/evidence rows for this run and compute a
    REAL grounding score from the fraction of claims that are supported.
    supports_claim / contradicts_claim are booleans; grounding_score is
    supported_count / total_claims, not a sampled proxy."""
    n_claims = int(rng.integers(2, 6))
    rows = []
    support_flags = []
    for k in range(1, n_claims + 1):
        evidence_id = f"{run_id}_ev{k:02d}"
        # successful/partial runs are more likely to have grounded claims;
        # a conflict flag makes contradiction more likely regardless of outcome
        base_support_p = {"success": 0.92, "partial_success": 0.65, "failed": 0.35}[final_status]
        if has_conflict_flag:
            base_support_p *= 0.75
        supports = bool(rng.random() < base_support_p)
        contradicts = bool((not supports) and rng.random() < (0.5 if has_conflict_flag else 0.2))
        support_flags.append(supports)
        rows.append({
            "evidence_id": evidence_id,
            "run_id": run_id,
            "task_id": task_row["task_id"],
            "source_type": rng.choice(["retrieved_document", "tool_output", "api_response"]),
            "claim": f"Claim {k} derived from {task_row['task_domain']} trajectory for {run_id}.",
            "relevance": round(float(rng.uniform(0.5, 1.0)), 3),
            "supports_claim": supports,
            "contradicts_claim": contradicts,
        })
    grounding_score = round(sum(support_flags) / len(support_flags), 3)
    return rows, grounding_score


def evaluate_run(run_id, task_row, steps, failure_rows, recovery_rows, final_status, grounding_score, rng):
    n_steps = len(steps)
    tool_calls = [s for s in steps if s["tool_name"] is not None]
    task_success = final_status in ("success", "partial_success")
    critical_failures = [f for f in failure_rows if f["is_critical"]]
    n_failures = len(failure_rows)
    n_cascading = sum(1 for f in failure_rows if f["is_cascading"])

    recovered_failures = {r["failure_id"] for r in recovery_rows if r["recovery_success"]}
    recovery_success_rate = (len(recovered_failures) / n_failures) if n_failures else None

    constraint_satisfaction = 1.0 if final_status == "success" else (0.5 if final_status == "partial_success" else 0.0)
    final_answer_score = round(constraint_satisfaction, 3)

    expected_tool_count = max(2, n_steps // 3)
    tool_efficiency = round(min(1.0, expected_tool_count / max(len(tool_calls), 1)), 3)
    trajectory_efficiency = round(min(1.0, 8 / max(n_steps, 1)), 3) if task_row["difficulty"] == "easy" else round(min(1.0, 14 / max(n_steps, 1)), 3)

    reliability_score = round(
        0.5 * (1.0 if task_success else 0.0)
        + 0.2 * (0.0 if critical_failures else 1.0)
        + 0.2 * (recovery_success_rate if recovery_success_rate is not None else 1.0)
        + 0.1 * tool_efficiency,
        3,
    )

    return {
        "run_id": run_id,
        "task_success": bool(task_success),
        "constraint_satisfaction": constraint_satisfaction,
        "failure_count": n_failures,
        "critical_failure_count": len(critical_failures),
        "cascading_failure_count": n_cascading,
        "recovery_success_rate": recovery_success_rate,
        "tool_efficiency": tool_efficiency,
        "trajectory_efficiency": trajectory_efficiency,
        "grounding_score": grounding_score,
        "final_answer_score": final_answer_score,
        "reliability_score": max(0.0, min(1.0, reliability_score)),
    }


def generate(n_tasks: int, runs_per_task: int, seed: int, out_dir: str, failure_prob: float) -> None:
    rng = np.random.default_rng(seed)

    agents_df, tools_df, taxonomy_df = build_reference_tables()
    tasks_df = make_tasks(rng, n_tasks)

    difficulty_len = {"easy": (4, 8), "medium": (7, 14), "hard": (12, 22)}
    recovery_success_base_rate = {
        "retry": 0.55, "alternative_tool": 0.65, "reformulate_query": 0.6,
        "verify_result": 0.7, "rollback": 0.6, "replan": 0.65,
        "ask_for_clarification": 0.75, "use_additional_evidence": 0.62,
        "change_execution_strategy": 0.58,
    }

    all_runs, all_steps, all_failures, all_recoveries, all_evals, all_evidence = [], [], [], [], [], []
    run_ctr = 1

    for _, task_row in tasks_df.iterrows():
        n_runs_this_task = rng.integers(1, runs_per_task + 1)
        chosen_agents = rng.choice(agents_df["agent_id"].values, size=n_runs_this_task, replace=False if n_runs_this_task <= len(agents_df) else True)
        for run_number, agent_id in enumerate(chosen_agents, start=1):
            run_id = f"run_{run_ctr:06d}"
            run_ctr += 1
            agent_row = agents_df[agents_df["agent_id"] == agent_id].iloc[0]

            steps, failure_rows, recovery_rows, final_status, has_conflict_flag = simulate_run(
                rng, run_id, task_row, agent_row, difficulty_len, failure_prob, recovery_success_base_rate
            )
            evidence_rows, grounding_score = make_evidence_for_run(rng, run_id, task_row, has_conflict_flag, final_status)

            tool_calls = [s for s in steps if s["tool_name"] is not None]
            latency_ms = int(sum(rng.integers(300, 4000) for _ in steps))
            input_tokens = int(sum(rng.integers(80, 600) for _ in steps))
            output_tokens = int(sum(rng.integers(20, 300) for _ in steps))
            for r in recovery_rows:
                if r["recovery_attempted"]:
                    latency_ms += r["recovery_latency_ms"]
                    output_tokens += r["recovery_token_cost"]

            final_answer = (
                f"Completed {task_row['task_domain']} task with {len(tool_calls)} tool calls."
                if final_status == "success"
                else f"Attempted {task_row['task_domain']} task; final status = {final_status}."
            )

            all_runs.append({
                "run_id": run_id,
                "task_id": task_row["task_id"],
                "agent_id": agent_id,
                "run_number": int(run_number),
                "start_time": None,
                "end_time": None,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "tool_call_count": len(tool_calls),
                "unique_tools_used": len(set(s["tool_name"] for s in tool_calls)),
                "available_tool_count": len(task_row["available_tools"].split(",")),
                "failure_count": len(failure_rows),
                "final_status": final_status,
                "final_answer": final_answer,
            })
            all_steps.extend(steps)
            all_failures.extend(failure_rows)
            all_recoveries.extend(recovery_rows)
            all_evidence.extend(evidence_rows)
            all_evals.append(evaluate_run(run_id, task_row, steps, failure_rows, recovery_rows, final_status, grounding_score, rng))

    runs_df = pd.DataFrame(all_runs)
    steps_df = pd.DataFrame(all_steps)
    failures_df = pd.DataFrame(all_failures)
    recoveries_df = pd.DataFrame(all_recoveries)
    evals_df = pd.DataFrame(all_evals)
    evidence_df = pd.DataFrame(all_evidence)

    # synthetic but internally consistent timestamps
    base_time = pd.Timestamp("2026-06-01T00:00:00Z")
    offsets = np.cumsum(rng.integers(30, 600, size=len(runs_df)))
    starts = [base_time + pd.Timedelta(seconds=int(o)) for o in offsets]
    ends = [s + pd.Timedelta(milliseconds=int(lat)) for s, lat in zip(starts, runs_df["latency_ms"])]
    runs_df["start_time"] = [s.isoformat() for s in starts]
    runs_df["end_time"] = [e.isoformat() for e in ends]

    os.makedirs(out_dir, exist_ok=True)
    tasks_df.to_csv(os.path.join(out_dir, "tasks.csv"), index=False)
    agents_df.to_csv(os.path.join(out_dir, "agents.csv"), index=False)
    tools_df.to_csv(os.path.join(out_dir, "tools.csv"), index=False)
    taxonomy_df.to_csv(os.path.join(out_dir, "taxonomy.csv"), index=False)
    runs_df.to_csv(os.path.join(out_dir, "agent_runs.csv"), index=False)
    steps_df.to_csv(os.path.join(out_dir, "trajectory_steps.csv"), index=False)
    failures_df.to_csv(os.path.join(out_dir, "failure_events.csv"), index=False)
    recoveries_df.to_csv(os.path.join(out_dir, "recovery_events.csv"), index=False)
    evals_df.to_csv(os.path.join(out_dir, "evaluations.csv"), index=False)
    evidence_df.to_csv(os.path.join(out_dir, "evidence.csv"), index=False)

    n_multi = (failures_df.groupby("run_id").size() > 1).sum() if len(failures_df) else 0
    n_cascading = int(failures_df["is_cascading"].sum()) if len(failures_df) else 0

    print(f"tasks:              {len(tasks_df)}")
    print(f"agents:             {len(agents_df)}")
    print(f"tools:              {len(tools_df)}")
    print(f"taxonomy entries:   {len(taxonomy_df)}")
    print(f"agent_runs:         {len(runs_df)}")
    print(f"trajectory_steps:   {len(steps_df)}")
    print(f"failure_events:     {len(failures_df)}")
    print(f"recovery_events:    {len(recoveries_df)}")
    print(f"evaluations:        {len(evals_df)}")
    print(f"evidence:           {len(evidence_df)}")
    print(f"success rate:       {(runs_df['final_status'] == 'success').mean():.1%}")
    print(f"failure rate:       {(runs_df['failure_count'] > 0).mean():.1%}")
    print(f"multi-failure runs: {n_multi} ({n_multi / len(runs_df):.1%} of runs)")
    print(f"cascading failures: {n_cascading} ({n_cascading / max(len(failures_df),1):.1%} of failures)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-tasks", type=int, default=900)
    ap.add_argument("--runs-per-task", type=int, default=4)
    ap.add_argument("--failure-prob", type=float, default=0.22)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default=os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    args = ap.parse_args()
    generate(args.n_tasks, args.runs_per_task, args.seed, args.out, args.failure_prob)
