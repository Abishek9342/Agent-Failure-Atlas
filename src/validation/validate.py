"""Data validation suite for Agent Failure Atlas 2026 (v2).

Checks referential integrity, primary-key uniqueness, required-field nulls,
enumeration membership, trajectory sequencing, numeric sanity, multi-failure
consistency, cascade consistency, and label-leakage across all ten tables.
Prints a human-readable report and writes reports/final_quality_report.md.
Exits non-zero if any check fails.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "generation"))
from taxonomy import (  # noqa: E402
    ACTION_TYPES, DECISION_CATEGORIES, RECOVERY_STRATEGIES, STEP_STATUSES,
    all_failure_types, cascade_targets,
)

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA_DIR = os.path.join(ROOT, "data")
REPORT_PATH = os.path.join(ROOT, "reports", "final_quality_report.md")

FAILURE_TYPES = set(all_failure_types())
RECOVERY_STRATEGY_NAMES = set(RECOVERY_STRATEGIES.keys())


def load_tables():
    names = ["tasks", "agents", "tools", "taxonomy", "agent_runs",
              "trajectory_steps", "failure_events", "recovery_events",
              "evaluations", "evidence"]
    return {n: pd.read_csv(os.path.join(DATA_DIR, f"{n}.csv")) for n in names}


class Checker:
    def __init__(self):
        self.results = []  # (check_name, status, detail)

    def check(self, name, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        self.results.append((name, status, detail))
        return condition

    @property
    def all_passed(self):
        return all(s == "PASS" for _, s, _ in self.results)


def run_validation(t: dict, c: Checker):
    tasks, agents, tools, taxonomy = t["tasks"], t["agents"], t["tools"], t["taxonomy"]
    runs, steps, failures, recoveries, evals, evidence = (
        t["agent_runs"], t["trajectory_steps"], t["failure_events"],
        t["recovery_events"], t["evaluations"], t["evidence"],
    )

    # --- Uniqueness of primary keys ---
    c.check("tasks.task_id unique", tasks["task_id"].is_unique)
    c.check("agents.agent_id unique", agents["agent_id"].is_unique)
    c.check("tools.tool_name unique", tools["tool_name"].is_unique)
    c.check("taxonomy.taxonomy_id unique", taxonomy["taxonomy_id"].is_unique)
    c.check("agent_runs.run_id unique", runs["run_id"].is_unique)
    c.check("trajectory_steps.step_id unique", steps["step_id"].is_unique)
    c.check("failure_events.failure_id unique", failures["failure_id"].is_unique)
    c.check("recovery_events.recovery_id unique", recoveries["recovery_id"].is_unique)
    c.check("evaluations.run_id unique", evals["run_id"].is_unique)
    c.check("evidence.evidence_id unique", evidence["evidence_id"].is_unique)

    # --- Referential integrity ---
    c.check("agent_runs.task_id -> tasks.task_id",
            runs["task_id"].isin(tasks["task_id"]).all())
    c.check("agent_runs.agent_id -> agents.agent_id",
            runs["agent_id"].isin(agents["agent_id"]).all())
    c.check("trajectory_steps.run_id -> agent_runs.run_id",
            steps["run_id"].isin(runs["run_id"]).all())
    c.check("failure_events.run_id -> agent_runs.run_id",
            failures["run_id"].isin(runs["run_id"]).all())
    c.check("failure_events.step_id -> trajectory_steps.step_id",
            failures["step_id"].isin(steps["step_id"]).all())
    c.check("recovery_events.run_id -> agent_runs.run_id",
            recoveries["run_id"].isin(runs["run_id"]).all())
    c.check("recovery_events.failure_id -> failure_events.failure_id",
            recoveries["failure_id"].isin(failures["failure_id"]).all())
    c.check("evaluations.run_id -> agent_runs.run_id",
            evals["run_id"].isin(runs["run_id"]).all())
    c.check("evidence.run_id -> agent_runs.run_id",
            evidence["run_id"].isin(runs["run_id"]).all())
    c.check("evidence.task_id -> tasks.task_id",
            evidence["task_id"].isin(tasks["task_id"]).all())
    steps_tool_ok = steps["tool_name"].isin(tools["tool_name"]) | steps["tool_name"].isna()
    c.check("trajectory_steps.tool_name -> tools.tool_name (or null)", steps_tool_ok.all())

    parent_ok = failures["parent_failure_id"].isna() | failures["parent_failure_id"].isin(failures["failure_id"])
    c.check("failure_events.parent_failure_id -> failure_events.failure_id (or null)", parent_ok.all())

    # every run has >=1 step, exactly one evaluation
    runs_with_steps = set(steps["run_id"])
    c.check("every agent_run has >=1 trajectory_steps", set(runs["run_id"]) <= runs_with_steps)
    c.check("every agent_run has exactly one evaluations row",
            (runs["run_id"].isin(evals["run_id"])).all() and evals["run_id"].is_unique)

    # --- Null validation on required fields ---
    required_not_null = {
        "tasks": ["task_id", "task_domain", "difficulty", "task_description", "success_criteria"],
        "agents": ["agent_id", "model", "provider", "capability_tier"],
        "agent_runs": ["run_id", "task_id", "agent_id", "final_status", "latency_ms"],
        "trajectory_steps": ["run_id", "step_id", "sequence_number", "action_type", "decision_category", "step_status"],
        "failure_events": ["failure_id", "run_id", "step_id", "failure_type", "failure_category", "severity", "severity_level", "failure_sequence"],
        "recovery_events": ["recovery_id", "failure_id", "run_id", "recovery_attempted", "final_outcome", "recovery_attempt_number"],
        "evaluations": ["run_id", "task_success", "reliability_score"],
        "evidence": ["evidence_id", "run_id", "task_id", "claim", "supports_claim"],
    }
    for tname, cols in required_not_null.items():
        df = t[tname]
        for col in cols:
            c.check(f"{tname}.{col} has no unexpected nulls", df[col].notna().all())

    # --- Enumeration validation ---
    c.check("trajectory_steps.decision_category in taxonomy",
            steps["decision_category"].isin(DECISION_CATEGORIES).all())
    c.check("trajectory_steps.action_type in taxonomy",
            steps["action_type"].isin(ACTION_TYPES).all())
    c.check("trajectory_steps.step_status in taxonomy",
            steps["step_status"].isin(STEP_STATUSES).all())
    c.check("failure_events.failure_type in taxonomy",
            failures["failure_type"].isin(FAILURE_TYPES).all())
    c.check("failure_events.severity_level in {1,2,3,4}",
            failures["severity_level"].isin([1, 2, 3, 4]).all())
    recovered_mask = recoveries["recovery_attempted"] == True  # noqa: E712
    c.check("recovery_events.recovery_strategy in taxonomy (when attempted)",
            recoveries.loc[recovered_mask, "recovery_strategy"].isin(RECOVERY_STRATEGY_NAMES).all())
    c.check("agent_runs.final_status in {success, partial_success, failed}",
            runs["final_status"].isin(["success", "partial_success", "failed"]).all())
    c.check("agents.capability_tier in {high, medium, low}",
            agents["capability_tier"].isin(["high", "medium", "low"]).all())

    # --- Sequence validation ---
    seq_ok = True
    for run_id, g in steps.groupby("run_id"):
        seqs = g.sort_values("sequence_number")["sequence_number"].tolist()
        if seqs != sorted(seqs) or len(seqs) != len(set(seqs)):
            seq_ok = False
            break
    c.check("trajectory_steps.sequence_number strictly ordered & unique per run", seq_ok)

    # --- Numerical validation ---
    c.check("agent_runs.latency_ms >= 0", (runs["latency_ms"] >= 0).all())
    c.check("agent_runs.input_tokens >= 0", (runs["input_tokens"] >= 0).all())
    c.check("agent_runs.output_tokens >= 0", (runs["output_tokens"] >= 0).all())
    c.check("agent_runs.total_tokens == input+output", (runs["total_tokens"] == runs["input_tokens"] + runs["output_tokens"]).all())
    c.check("agent_runs.tool_call_count >= 0", (runs["tool_call_count"] >= 0).all())
    c.check("agent_runs.unique_tools_used <= tool_call_count", (runs["unique_tools_used"] <= runs["tool_call_count"]).all())
    c.check("recovery_events.recovery_latency_ms >= 0", (recoveries["recovery_latency_ms"] >= 0).all())
    c.check("recovery_events.recovery_token_cost >= 0", (recoveries["recovery_token_cost"] >= 0).all())
    c.check("recovery_events.recovery_attempt_number >= 0", (recoveries["recovery_attempt_number"] >= 0).all())
    c.check("evidence.relevance within [0,1]", evidence["relevance"].between(0, 1).all())
    for col in ["constraint_satisfaction", "grounding_score", "final_answer_score", "reliability_score", "tool_efficiency", "trajectory_efficiency"]:
        c.check(f"evaluations.{col} within [0,1]", evals[col].dropna().between(0, 1).all())
    c.check("evaluations.recovery_success_rate within [0,1] or null",
            evals["recovery_success_rate"].dropna().between(0, 1).all())

    # --- Duplicate checks ---
    c.check("no fully duplicate rows in trajectory_steps", not steps.duplicated().any())
    c.check("no fully duplicate rows in agent_runs", not runs.duplicated().any())
    c.check("no fully duplicate rows in failure_events", not failures.duplicated().any())

    # --- failure_count consistency ---
    fc_from_events = failures.groupby("run_id").size()
    fc_declared = runs.set_index("run_id")["failure_count"]
    merged = fc_declared.to_frame("declared").join(fc_from_events.to_frame("actual"), how="left").fillna(0)
    c.check("agent_runs.failure_count matches count of failure_events per run",
            (merged["declared"] == merged["actual"]).all())

    # --- Multi-failure consistency: failure_sequence ordering per run ---
    seq_ok = True
    for run_id, g in failures.groupby("run_id"):
        seqs = g.sort_values("failure_sequence")["failure_sequence"].tolist()
        if seqs != list(range(1, len(seqs) + 1)):
            seq_ok = False
            break
    c.check("failure_events.failure_sequence forms 1..N per run with no gaps/dupes", seq_ok)

    # --- Cascade consistency ---
    cascading = failures[failures["is_cascading"]]
    c.check("every is_cascading=True failure has a non-null parent_failure_id",
            cascading["parent_failure_id"].notna().all())
    non_cascading = failures[~failures["is_cascading"]]
    c.check("every is_cascading=False failure has a null parent_failure_id",
            non_cascading["parent_failure_id"].isna().all())
    # parent must belong to the same run
    fail_run_map = failures.set_index("failure_id")["run_id"]
    parent_same_run = cascading.apply(
        lambda r: fail_run_map.get(r["parent_failure_id"]) == r["run_id"], axis=1
    )
    c.check("cascading failure's parent_failure_id belongs to the same run", parent_same_run.all())
    # parent must precede child in failure_sequence
    fail_seq_map = failures.set_index("failure_id")["failure_sequence"]
    parent_precedes = cascading.apply(
        lambda r: fail_seq_map.get(r["parent_failure_id"], -1) < r["failure_sequence"], axis=1
    )
    c.check("cascading failure's parent_failure_id precedes it in failure_sequence", parent_precedes.all())
    # cascade edge must be a documented taxonomy relationship
    parent_type_map = failures.set_index("failure_id")["failure_type"]
    cascade_type_valid = cascading.apply(
        lambda r: r["failure_type"] in cascade_targets(parent_type_map.get(r["parent_failure_id"], "")), axis=1
    )
    c.check("cascading failure_type is a documented FAILURE_CASCADES edge from its parent's failure_type",
            cascade_type_valid.all())

    # --- Recovery consistency: attempt numbers per failure form 0 or 1..N ---
    attempt_ok = True
    for failure_id, g in recoveries.groupby("failure_id"):
        nums = sorted(g["recovery_attempt_number"].tolist())
        if nums != [0] and nums != list(range(1, len(nums) + 1)):
            attempt_ok = False
            break
    c.check("recovery_events.recovery_attempt_number is [0] (not attempted) or 1..N per failure", attempt_ok)

    # --- Failure step_status consistency ---
    steps_idx = steps.set_index("step_id")
    fail_step_status = steps_idx.loc[failures["step_id"], "step_status"]
    c.check("every failure_events.step_id has step_status in {error, recovered}",
            fail_step_status.isin(["error", "recovered"]).all())

    # --- Leakage detection ---
    ok_steps = steps[steps["step_status"] == "ok"]
    leak_mask = ok_steps["observation"].astype(str).str.contains("Failure detected", case=False, na=False)
    c.check("no step with step_status='ok' contains failure-indicating text in observation",
            not leak_mask.any())
    # noisy near-miss texture must appear on both failing and non-failing runs (not a leak proxy)
    noisy_mask = steps["observation"].astype(str).str.contains(
        "timeout|rate limited|malformed|schema mismatch|stale cache|partial response", case=False, na=False)
    noisy_runs = set(steps.loc[noisy_mask, "run_id"])
    failing_runs = set(failures["run_id"])
    c.check("noisy near-miss step text occurs in both failing and non-failing runs (not a leakage proxy)",
            len(noisy_runs - failing_runs) > 0 and len(noisy_runs & failing_runs) > 0)

    # --- Evidence / grounding consistency ---
    grounding_from_evidence = evidence.groupby("run_id")["supports_claim"].mean().round(3)
    grounding_declared = evals.set_index("run_id")["grounding_score"]
    ge_merged = grounding_declared.to_frame("declared").join(grounding_from_evidence.to_frame("actual"), how="left")
    c.check("evaluations.grounding_score matches mean(evidence.supports_claim) for its run",
            (ge_merged["declared"] == ge_merged["actual"]).all())


def distribution_summary(t: dict) -> str:
    runs, failures, recoveries, tasks, agents = t["agent_runs"], t["failure_events"], t["recovery_events"], t["tasks"], t["agents"]
    lines = []
    lines.append(f"- Total tasks: {len(tasks)}")
    lines.append(f"- Total agent_runs (trajectories): {len(runs)}")
    lines.append(f"- Total trajectory_steps: {len(t['trajectory_steps'])}")
    lines.append(f"- Total failure_events: {len(failures)}")
    lines.append(f"- Total recovery_events: {len(recoveries)}")
    lines.append(f"- Total evidence rows: {len(t['evidence'])}")
    lines.append(f"- final_status distribution: {runs['final_status'].value_counts().to_dict()}")
    lines.append(f"- runs with >=1 failure: {(runs['failure_count'] > 0).mean():.1%}")
    lines.append(f"- runs with >=2 failures (multi-failure): {(runs['failure_count'] > 1).mean():.1%}")
    lines.append(f"- clean success (no failure): {((runs['final_status']=='success') & (runs['failure_count']==0)).mean():.1%}")
    if len(failures):
        lines.append(f"- failure_category distribution: {failures['failure_category'].value_counts().to_dict()}")
        lines.append(f"- cascading failures: {failures['is_cascading'].sum()} ({failures['is_cascading'].mean():.1%} of all failures)")
        lines.append(f"- severity_level distribution: {failures['severity_level'].value_counts().sort_index().to_dict()}")
    if len(recoveries):
        attempted = recoveries[recoveries["recovery_attempted"] == True]  # noqa: E712
        if len(attempted):
            lines.append(f"- recovery success rate (when attempted): {attempted['recovery_success'].mean():.1%}")
            lines.append(f"- recovery attempts >1 (repeated recovery): {(attempted['recovery_attempt_number'] > 1).sum()}")
    lines.append(f"- domain distribution: {tasks['task_domain'].value_counts().to_dict()}")
    lines.append(f"- difficulty distribution: {tasks['difficulty'].value_counts().to_dict()}")
    lines.append(f"- model distribution: {runs.merge(agents, on='agent_id')['model'].value_counts().to_dict()}")
    return "\n".join(lines)


def write_report(c: Checker, t: dict):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    n_pass = sum(1 for _, s, _ in c.results if s == "PASS")
    n_fail = sum(1 for _, s, _ in c.results if s == "FAIL")
    lines = ["# Final Quality Report — Agent Failure Atlas 2026 (v2)", "",
             f"Checks run: {len(c.results)} | Passed: {n_pass} | Failed: {n_fail}", "",
             "## Dataset statistics", "", distribution_summary(t), "",
             "## Validation checks", "", "| Check | Status |", "|---|---|"]
    for name, status, detail in c.results:
        lines.append(f"| {name} | {status} |")
    lines += ["", "## Publication Readiness", "", "```", "READY" if c.all_passed else "NOT READY", "```"]
    if not c.all_passed:
        lines += ["", "Failed checks:", ""]
        lines += [f"- {name}: {detail}" for name, status, detail in c.results if status == "FAIL"]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return REPORT_PATH


if __name__ == "__main__":
    t = load_tables()
    c = Checker()
    run_validation(t, c)
    path = write_report(c, t)
    n_pass = sum(1 for _, s, _ in c.results if s == "PASS")
    n_fail = sum(1 for _, s, _ in c.results if s == "FAIL")
    print(f"Validation: {n_pass} passed, {n_fail} failed. Report written to {path}")
    if n_fail:
        for name, status, detail in c.results:
            if status == "FAIL":
                print(f"  FAIL: {name} {detail}")
        sys.exit(1)
