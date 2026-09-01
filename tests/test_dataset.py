"""Pytest wrapper around the validation suite, plus a few targeted schema tests."""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src", "validation"))
sys.path.insert(0, os.path.join(ROOT, "src", "generation"))

from validate import Checker, load_tables, run_validation  # noqa: E402


@pytest.fixture(scope="module")
def tables():
    return load_tables()


def test_all_validation_checks_pass(tables):
    c = Checker()
    run_validation(tables, c)
    failed = [(name, detail) for name, status, detail in c.results if status == "FAIL"]
    assert not failed, f"Validation failures: {failed}"


def test_expected_files_present():
    expected = ["tasks.csv", "agents.csv", "tools.csv", "taxonomy.csv", "agent_runs.csv",
                "trajectory_steps.csv", "failure_events.csv", "recovery_events.csv",
                "evaluations.csv", "evidence.csv"]
    data_dir = os.path.join(ROOT, "data")
    for fname in expected:
        assert os.path.exists(os.path.join(data_dir, fname)), f"missing {fname}"


def test_no_chain_of_thought_leak(tables):
    """observation/tool_output fields should be short, templated strings, not free-form reasoning traces."""
    steps = tables["trajectory_steps"]
    long_free_text = steps["observation"].dropna().str.len() > 400
    assert not long_free_text.any(), "trajectory_steps.observation contains suspiciously long free text"


def test_recovery_only_for_recoverable_or_attempted_flag_consistent(tables):
    recoveries = tables["recovery_events"]
    not_attempted = recoveries[recoveries["recovery_attempted"] == False]  # noqa: E712
    assert (not_attempted["recovery_success"] == False).all()  # noqa: E712
    assert (not_attempted["recovery_steps"] == 0).all()


def test_failure_step_status_is_error_or_recovered(tables):
    failures = tables["failure_events"]
    steps = tables["trajectory_steps"].set_index("step_id")
    statuses = steps.loc[failures["step_id"], "step_status"]
    assert statuses.isin(["error", "recovered"]).all()


def test_multi_failure_trajectories_exist(tables):
    """v2 must allow more than one diagnosed failure per trajectory."""
    runs = tables["agent_runs"]
    assert (runs["failure_count"] > 1).any(), "no multi-failure trajectories generated"
    assert (runs["failure_count"] == 0).any(), "no clean (zero-failure) trajectories generated"
    assert (runs["failure_count"] == 1).any(), "no single-failure trajectories generated"


def test_failure_ordering_per_run(tables):
    failures = tables["failure_events"]
    for run_id, g in failures.groupby("run_id"):
        seqs = g.sort_values("failure_sequence")["failure_sequence"].tolist()
        assert seqs == list(range(1, len(seqs) + 1)), f"non-contiguous failure_sequence in {run_id}: {seqs}"


def test_cascade_relationships_valid(tables):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "generation"))
    from taxonomy import cascade_targets

    failures = tables["failure_events"]
    cascading = failures[failures["is_cascading"]]
    assert len(cascading) > 0, "no cascading failures generated"
    type_by_id = failures.set_index("failure_id")["failure_type"]
    run_by_id = failures.set_index("failure_id")["run_id"]
    for _, row in cascading.iterrows():
        parent_id = row["parent_failure_id"]
        assert pd.notna(parent_id), "cascading failure missing parent_failure_id"
        assert run_by_id[parent_id] == row["run_id"], "cascade parent from a different run"
        assert row["failure_type"] in cascade_targets(type_by_id[parent_id]), \
            f"{row['failure_type']} is not a documented cascade target of {type_by_id[parent_id]}"


def test_recovery_sequences_valid(tables):
    recoveries = tables["recovery_events"]
    for failure_id, g in recoveries.groupby("failure_id"):
        nums = sorted(g["recovery_attempt_number"].tolist())
        assert nums == [0] or nums == list(range(1, len(nums) + 1)), \
            f"bad recovery_attempt_number sequence for {failure_id}: {nums}"


def test_evidence_relationships(tables):
    evidence = tables["evidence"]
    evals = tables["evaluations"].set_index("run_id")
    assert len(evidence) > 0
    assert evidence["run_id"].isin(evals.index).all()
    computed = evidence.groupby("run_id")["supports_claim"].mean().round(3)
    declared = evals.loc[computed.index, "grounding_score"]
    assert (computed.values == declared.values).all(), \
        "evaluations.grounding_score does not match evidence-derived support fraction"


def test_no_label_leakage_in_pre_failure_steps(tables):
    steps = tables["trajectory_steps"]
    ok_steps = steps[steps["step_status"] == "ok"]
    assert not ok_steps["observation"].astype(str).str.contains("Failure detected", case=False, na=False).any()


def test_pre_and_post_failure_features_distinguishable(tables):
    """Sanity check that agent_runs carries only pre/whole-run aggregate
    features (no column literally named after post-hoc diagnosis), and that
    trajectory-shape features used by the failure-prediction notebook do not
    include the failure/recovery tables' own columns."""
    runs = tables["agent_runs"]
    leaking_cols = {"failure_type", "failure_category", "recovery_strategy", "recovery_success"}
    assert not (leaking_cols & set(runs.columns)), \
        f"agent_runs contains post-failure diagnostic columns: {leaking_cols & set(runs.columns)}"


def test_taxonomy_consistency(tables):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "generation"))
    from taxonomy import all_failure_types, failure_category_of

    taxonomy = tables["taxonomy"]
    failures = tables["failure_events"]
    valid_types = set(all_failure_types())
    assert set(failures["failure_type"]) <= valid_types
    assert set(taxonomy["level_2"]) == valid_types
    for _, row in failures.drop_duplicates("failure_type").iterrows():
        assert failure_category_of(row["failure_type"]) == row["failure_category"]
