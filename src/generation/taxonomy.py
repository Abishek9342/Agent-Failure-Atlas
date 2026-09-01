"""Canonical failure and recovery taxonomies for Agent Failure Atlas 2026.

Single source of truth: the generator, validator, and docs/taxonomy.md are
all derived from this module so the published data and documentation can
never drift apart.
"""

# level_1 -> {level_2 -> (definition, example, severity_guidance, recoverable_typically)}
FAILURE_TAXONOMY = {
    "planning": {
        "incorrect_decomposition": (
            "The agent splits the task into sub-goals that do not, even if all completed, satisfy the original request.",
            "Task asks to reconcile two files; agent plans only to summarize one of them.",
            "moderate-high", True,
        ),
        "premature_execution": (
            "The agent takes an execution action before gathering information required to do it correctly.",
            "Agent calls a write/update tool before reading the current state it needs to update.",
            "moderate", True,
        ),
        "missing_prerequisite": (
            "The plan omits a step whose output a later step depends on.",
            "Agent tries to filter records by a field it never fetched.",
            "moderate", True,
        ),
        "wrong_sequence": (
            "Necessary steps are present but ordered so that a later step cannot use an earlier step's output correctly.",
            "Agent validates a computed total before the computation step has run.",
            "low-moderate", True,
        ),
    },
    "tool_use": {
        "wrong_tool": (
            "The agent selects a tool that cannot accomplish the current sub-goal.",
            "Agent calls a calculator tool to answer a lookup question that requires retrieval.",
            "moderate", True,
        ),
        "wrong_arguments": (
            "The correct tool is selected but called with malformed, mistyped, or semantically incorrect arguments.",
            "Agent passes a string where the tool schema requires a date in ISO format.",
            "low-moderate", True,
        ),
        "tool_misuse": (
            "The tool is used in a way that violates its documented contract or intended use.",
            "Agent uses a read-only search tool's raw query field to attempt a write operation.",
            "moderate", True,
        ),
        "repeated_tool_call": (
            "The agent calls the same tool with the same or near-identical arguments more than once without new information justifying it.",
            "Agent re-issues an identical search query after already receiving results for it.",
            "low", True,
        ),
        "tool_loop": (
            "The agent enters a cycle of tool calls that does not converge toward task completion.",
            "Agent alternates between two tools for many steps without the trajectory state changing.",
            "high", False,
        ),
    },
    "retrieval": {
        "retrieval_miss": (
            "A retrieval/search action fails to surface information that was available and necessary.",
            "Agent searches with terms too narrow to match the document containing the answer.",
            "moderate", True,
        ),
        "irrelevant_retrieval": (
            "Retrieved content is topically unrelated to the information need.",
            "Agent's query returns documents about a different but similarly named entity.",
            "low-moderate", True,
        ),
        "stale_information": (
            "The agent relies on retrieved information that was superseded by more recent, contradicting information available in the same session.",
            "Agent uses an early tool result after a later tool call already corrected it.",
            "moderate", True,
        ),
        "context_conflict": (
            "Two retrieved sources disagree and the agent does not detect or resolve the conflict.",
            "Agent combines figures from two documents that use incompatible definitions.",
            "moderate-high", True,
        ),
    },
    "reasoning": {
        "logical_error": (
            "The agent's derivation contains an invalid logical step.",
            "Agent concludes B follows from A when the retrieved evidence only supports 'A is possible'.",
            "moderate", True,
        ),
        "constraint_violation": (
            "The final answer or an intermediate step violates an explicit task constraint.",
            "Task caps a budget field at 5 items; agent returns 7.",
            "moderate-high", True,
        ),
        "incorrect_inference": (
            "The agent draws a conclusion not supported by the available evidence.",
            "Agent infers a company is profitable from a single quarter's revenue figure alone.",
            "moderate", True,
        ),
        "numerical_error": (
            "An arithmetic or unit computation is wrong.",
            "Agent sums a percentage column instead of computing a weighted average.",
            "moderate", True,
        ),
    },
    "state": {
        "state_tracking_error": (
            "The agent's internal representation of task progress diverges from the actual trajectory state.",
            "Agent believes a file has already been created when the create call actually failed.",
            "moderate-high", True,
        ),
        "memory_failure": (
            "The agent fails to carry forward information established earlier in the same run.",
            "Agent re-asks for a constraint the task description already specified.",
            "low-moderate", True,
        ),
        "lost_context": (
            "Long trajectories cause earlier, still-relevant context to no longer influence later decisions.",
            "Agent's final answer ignores a constraint stated in step 2 of a 40-step run.",
            "moderate", True,
        ),
    },
    "verification": {
        "failure_to_verify": (
            "The agent skips an available verification step before finalizing.",
            "Agent produces a computed answer without checking it against the source data.",
            "moderate", True,
        ),
        "false_verification": (
            "The agent runs a verification step but the check itself is flawed and passes incorrect work.",
            "Agent 'verifies' a total by re-running the same buggy computation.",
            "high", False,
        ),
        "unsupported_conclusion": (
            "The agent presents a conclusion as verified when no verification actually occurred.",
            "Agent states 'confirmed against source' with no corresponding verification step in the trajectory.",
            "high", False,
        ),
    },
    "execution": {
        "partial_execution": (
            "A multi-part action only partially completes and the agent proceeds as if it fully completed.",
            "Agent updates 3 of 5 required records, then reports the update as done.",
            "moderate-high", True,
        ),
        "failed_execution": (
            "An execution action returns an error and the agent's trajectory does not account for it.",
            "Tool call errors out; agent's next step ignores the error and proceeds as though it succeeded.",
            "moderate-high", True,
        ),
        "unauthorized_action": (
            "The agent takes an action outside the scope granted by the task's stated constraints.",
            "Task restricts the agent to read-only tools; agent invokes a write-capable tool anyway.",
            "critical", False,
        ),
    },
    "output": {
        "incorrect_final_answer": (
            "The final answer does not match the ground truth for the task.",
            "Numeric answer off from the ground-truth value.",
            "high", True,
        ),
        "incomplete_answer": (
            "The final answer addresses only part of a multi-part task.",
            "Task asks for three deliverables; final answer supplies one.",
            "moderate", True,
        ),
        "hallucinated_result": (
            "The final answer includes specific claims not traceable to any tool observation in the trajectory.",
            "Agent cites a figure that never appeared in any retrieved document.",
            "critical", False,
        ),
        "claimed_success_after_failure": (
            "The agent reports task success despite the trajectory containing an unresolved critical failure.",
            "A required write action failed with an error, but the final answer says 'completed successfully'.",
            "critical", False,
        ),
    },
}

RECOVERY_STRATEGIES = {
    "retry": "Re-attempt the identical action unchanged, on the assumption the failure was transient.",
    "alternative_tool": "Switch to a different tool capable of achieving the same sub-goal.",
    "reformulate_query": "Re-issue a retrieval/search action with revised query terms.",
    "verify_result": "Insert an explicit verification step before proceeding or finalizing.",
    "rollback": "Undo or discard a partially completed action before re-attempting.",
    "replan": "Discard the current plan and construct a new decomposition of the task.",
    "ask_for_clarification": "Surface a request for additional information instead of guessing.",
    "use_additional_evidence": "Gather further supporting information rather than repeating the failed action.",
    "change_execution_strategy": "Alter how a step is executed (e.g. different arguments, narrower scope) without changing tools.",
}

DECISION_CATEGORIES = [
    "planning", "retrieval", "tool_selection", "execution",
    "verification", "correction", "finalization",
]

ACTION_TYPES = ["plan", "tool_call", "observe", "verify", "correct", "finalize"]

STEP_STATUSES = ["ok", "error", "recovered", "failed"]

SEVERITY_LEVELS = ["low", "low-moderate", "moderate", "moderate-high", "high", "critical"]

# Numeric severity rubric (docs/taxonomy.md renders this). This is the
# documented criteria referenced by every failure_events.severity value —
# severity is not assigned arbitrarily per-occurrence, it is inherited from
# the failure type's taxonomy entry (see FAILURE_TAXONOMY severity_guidance
# above), which in turn follows this rubric.
SEVERITY_RUBRIC = {
    1: ("minor", "low",
        "Cosmetic or easily-corrected deviation. Does not affect whether the "
        "task can ultimately succeed; a single retry or reformulation "
        "typically resolves it."),
    2: ("moderate", "low-moderate / moderate",
        "Meaningfully derails the current step but not the overall plan. "
        "Recoverable via a standard strategy (retry, alternative_tool, "
        "verify_result) without discarding prior progress."),
    3: ("major", "moderate-high / high",
        "Invalidates part of the trajectory's prior work or risks an "
        "incorrect final answer if unaddressed. Recovery typically requires "
        "replanning, rollback, or additional evidence gathering, and is not "
        "guaranteed to succeed."),
    4: ("critical", "critical",
        "The agent's own signal about task state is untrustworthy (a false "
        "verification, an unauthorized action, a hallucinated or falsely "
        "claimed-successful result). No recovery strategy can be trusted to "
        "act on corrupted self-assessment, so these are treated as "
        "typically unrecoverable in this dataset by construction."),
}

# Cascade edges: failure_type -> plausible downstream failure_type(s) it can
# directly cause. Used to generate multi-failure trajectories where a later
# failure is causally linked to an earlier one (failure_events.parent_failure_id)
# rather than sampled independently. Edges only point to failure types whose
# category is reachable from a later decision_category than the parent's
# typical one, keeping cascades directionally realistic (e.g. a retrieval
# problem can cause a downstream reasoning/output problem, not vice versa).
FAILURE_CASCADES = {
    "retrieval_miss": ["incorrect_inference", "unsupported_conclusion", "incomplete_answer"],
    "irrelevant_retrieval": ["incorrect_inference", "logical_error"],
    "stale_information": ["context_conflict", "incorrect_final_answer"],
    "context_conflict": ["unsupported_conclusion", "incorrect_inference"],
    "wrong_tool": ["partial_execution", "failed_execution"],
    "wrong_arguments": ["failed_execution", "partial_execution"],
    "tool_misuse": ["failed_execution", "state_tracking_error"],
    "incorrect_decomposition": ["missing_prerequisite", "incomplete_answer"],
    "missing_prerequisite": ["premature_execution", "failed_execution"],
    "premature_execution": ["state_tracking_error", "failed_execution"],
    "logical_error": ["incorrect_inference", "incorrect_final_answer"],
    "incorrect_inference": ["unsupported_conclusion", "incorrect_final_answer"],
    "numerical_error": ["incorrect_final_answer", "constraint_violation"],
    "state_tracking_error": ["lost_context", "claimed_success_after_failure"],
    "memory_failure": ["constraint_violation", "incomplete_answer"],
    "failure_to_verify": ["unsupported_conclusion", "incorrect_final_answer"],
    "partial_execution": ["incomplete_answer", "claimed_success_after_failure"],
    "failed_execution": ["claimed_success_after_failure", "incomplete_answer"],
}


def cascade_targets(failure_type: str):
    """Plausible downstream failure types this failure type can directly cause."""
    return FAILURE_CASCADES.get(failure_type, [])


def iter_taxonomy_rows():
    """Yield flattened (level_1, level_2, definition, example, severity_guidance, recoverable_typically) tuples."""
    for level_1, entries in FAILURE_TAXONOMY.items():
        for level_2, (definition, example, severity, recoverable) in entries.items():
            yield level_1, level_2, definition, example, severity, recoverable


def all_failure_types():
    return [l2 for l1, entries in FAILURE_TAXONOMY.items() for l2 in entries]


def failure_category_of(failure_type: str) -> str:
    for level_1, entries in FAILURE_TAXONOMY.items():
        if failure_type in entries:
            return level_1
    raise KeyError(failure_type)


# severity text (as stored in FAILURE_TAXONOMY) -> numeric rubric level (1-4).
# A "low-moderate" style compound band maps to the lower of the two levels it
# spans, since severity_guidance describes a typical *range*, while the
# per-occurrence severity actually assigned always resolves to one concrete
# rubric level.
_SEVERITY_TEXT_TO_LEVEL = {
    "low": 1,
    "low-moderate": 1,
    "moderate": 2,
    "moderate-high": 3,
    "high": 3,
    "critical": 4,
}


def severity_level(severity_text: str) -> int:
    return _SEVERITY_TEXT_TO_LEVEL[severity_text]
