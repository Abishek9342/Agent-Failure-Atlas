# Failure & Recovery Taxonomy — Agent Failure Atlas 2026 (v2)

This is the canonical taxonomy. It is generated from `src/generation/taxonomy.py`, the single source of truth also used by the generator and the validator — so this document can never drift out of sync with the published data.

## Severity rubric

Every `failure_events.severity` value is inherited from its failure type's documented `severity_guidance` below, which in turn follows this numeric rubric (`failure_events.severity_level`, 1-4). Severity is never assigned arbitrarily per-occurrence.

**Level 1 — minor** (`severity_guidance` ≈ low)
- Cosmetic or easily-corrected deviation. Does not affect whether the task can ultimately succeed; a single retry or reformulation typically resolves it.

**Level 2 — moderate** (`severity_guidance` ≈ low-moderate / moderate)
- Meaningfully derails the current step but not the overall plan. Recoverable via a standard strategy (retry, alternative_tool, verify_result) without discarding prior progress.

**Level 3 — major** (`severity_guidance` ≈ moderate-high / high)
- Invalidates part of the trajectory's prior work or risks an incorrect final answer if unaddressed. Recovery typically requires replanning, rollback, or additional evidence gathering, and is not guaranteed to succeed.

**Level 4 — critical** (`severity_guidance` ≈ critical)
- The agent's own signal about task state is untrustworthy (a false verification, an unauthorized action, a hallucinated or falsely claimed-successful result). No recovery strategy can be trusted to act on corrupted self-assessment, so these are treated as typically unrecoverable in this dataset by construction.

## Failure taxonomy

### planning

**`incorrect_decomposition`**
- Definition: The agent splits the task into sub-goals that do not, even if all completed, satisfy the original request.
- Example: Task asks to reconcile two files; agent plans only to summarize one of them.
- Typical severity: moderate-high
- Typically recoverable: True
- Documented cascade targets (can directly cause): `missing_prerequisite`, `incomplete_answer`

**`premature_execution`**
- Definition: The agent takes an execution action before gathering information required to do it correctly.
- Example: Agent calls a write/update tool before reading the current state it needs to update.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `state_tracking_error`, `failed_execution`

**`missing_prerequisite`**
- Definition: The plan omits a step whose output a later step depends on.
- Example: Agent tries to filter records by a field it never fetched.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `premature_execution`, `failed_execution`

**`wrong_sequence`**
- Definition: Necessary steps are present but ordered so that a later step cannot use an earlier step's output correctly.
- Example: Agent validates a computed total before the computation step has run.
- Typical severity: low-moderate
- Typically recoverable: True

### tool_use

**`wrong_tool`**
- Definition: The agent selects a tool that cannot accomplish the current sub-goal.
- Example: Agent calls a calculator tool to answer a lookup question that requires retrieval.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `partial_execution`, `failed_execution`

**`wrong_arguments`**
- Definition: The correct tool is selected but called with malformed, mistyped, or semantically incorrect arguments.
- Example: Agent passes a string where the tool schema requires a date in ISO format.
- Typical severity: low-moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `failed_execution`, `partial_execution`

**`tool_misuse`**
- Definition: The tool is used in a way that violates its documented contract or intended use.
- Example: Agent uses a read-only search tool's raw query field to attempt a write operation.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `failed_execution`, `state_tracking_error`

**`repeated_tool_call`**
- Definition: The agent calls the same tool with the same or near-identical arguments more than once without new information justifying it.
- Example: Agent re-issues an identical search query after already receiving results for it.
- Typical severity: low
- Typically recoverable: True

**`tool_loop`**
- Definition: The agent enters a cycle of tool calls that does not converge toward task completion.
- Example: Agent alternates between two tools for many steps without the trajectory state changing.
- Typical severity: high
- Typically recoverable: False

### retrieval

**`retrieval_miss`**
- Definition: A retrieval/search action fails to surface information that was available and necessary.
- Example: Agent searches with terms too narrow to match the document containing the answer.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `incorrect_inference`, `unsupported_conclusion`, `incomplete_answer`

**`irrelevant_retrieval`**
- Definition: Retrieved content is topically unrelated to the information need.
- Example: Agent's query returns documents about a different but similarly named entity.
- Typical severity: low-moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `incorrect_inference`, `logical_error`

**`stale_information`**
- Definition: The agent relies on retrieved information that was superseded by more recent, contradicting information available in the same session.
- Example: Agent uses an early tool result after a later tool call already corrected it.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `context_conflict`, `incorrect_final_answer`

**`context_conflict`**
- Definition: Two retrieved sources disagree and the agent does not detect or resolve the conflict.
- Example: Agent combines figures from two documents that use incompatible definitions.
- Typical severity: moderate-high
- Typically recoverable: True
- Documented cascade targets (can directly cause): `unsupported_conclusion`, `incorrect_inference`

### reasoning

**`logical_error`**
- Definition: The agent's derivation contains an invalid logical step.
- Example: Agent concludes B follows from A when the retrieved evidence only supports 'A is possible'.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `incorrect_inference`, `incorrect_final_answer`

**`constraint_violation`**
- Definition: The final answer or an intermediate step violates an explicit task constraint.
- Example: Task caps a budget field at 5 items; agent returns 7.
- Typical severity: moderate-high
- Typically recoverable: True

**`incorrect_inference`**
- Definition: The agent draws a conclusion not supported by the available evidence.
- Example: Agent infers a company is profitable from a single quarter's revenue figure alone.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `unsupported_conclusion`, `incorrect_final_answer`

**`numerical_error`**
- Definition: An arithmetic or unit computation is wrong.
- Example: Agent sums a percentage column instead of computing a weighted average.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `incorrect_final_answer`, `constraint_violation`

### state

**`state_tracking_error`**
- Definition: The agent's internal representation of task progress diverges from the actual trajectory state.
- Example: Agent believes a file has already been created when the create call actually failed.
- Typical severity: moderate-high
- Typically recoverable: True
- Documented cascade targets (can directly cause): `lost_context`, `claimed_success_after_failure`

**`memory_failure`**
- Definition: The agent fails to carry forward information established earlier in the same run.
- Example: Agent re-asks for a constraint the task description already specified.
- Typical severity: low-moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `constraint_violation`, `incomplete_answer`

**`lost_context`**
- Definition: Long trajectories cause earlier, still-relevant context to no longer influence later decisions.
- Example: Agent's final answer ignores a constraint stated in step 2 of a 40-step run.
- Typical severity: moderate
- Typically recoverable: True

### verification

**`failure_to_verify`**
- Definition: The agent skips an available verification step before finalizing.
- Example: Agent produces a computed answer without checking it against the source data.
- Typical severity: moderate
- Typically recoverable: True
- Documented cascade targets (can directly cause): `unsupported_conclusion`, `incorrect_final_answer`

**`false_verification`**
- Definition: The agent runs a verification step but the check itself is flawed and passes incorrect work.
- Example: Agent 'verifies' a total by re-running the same buggy computation.
- Typical severity: high
- Typically recoverable: False

**`unsupported_conclusion`**
- Definition: The agent presents a conclusion as verified when no verification actually occurred.
- Example: Agent states 'confirmed against source' with no corresponding verification step in the trajectory.
- Typical severity: high
- Typically recoverable: False

### execution

**`partial_execution`**
- Definition: A multi-part action only partially completes and the agent proceeds as if it fully completed.
- Example: Agent updates 3 of 5 required records, then reports the update as done.
- Typical severity: moderate-high
- Typically recoverable: True
- Documented cascade targets (can directly cause): `incomplete_answer`, `claimed_success_after_failure`

**`failed_execution`**
- Definition: An execution action returns an error and the agent's trajectory does not account for it.
- Example: Tool call errors out; agent's next step ignores the error and proceeds as though it succeeded.
- Typical severity: moderate-high
- Typically recoverable: True
- Documented cascade targets (can directly cause): `claimed_success_after_failure`, `incomplete_answer`

**`unauthorized_action`**
- Definition: The agent takes an action outside the scope granted by the task's stated constraints.
- Example: Task restricts the agent to read-only tools; agent invokes a write-capable tool anyway.
- Typical severity: critical
- Typically recoverable: False

### output

**`incorrect_final_answer`**
- Definition: The final answer does not match the ground truth for the task.
- Example: Numeric answer off from the ground-truth value.
- Typical severity: high
- Typically recoverable: True

**`incomplete_answer`**
- Definition: The final answer addresses only part of a multi-part task.
- Example: Task asks for three deliverables; final answer supplies one.
- Typical severity: moderate
- Typically recoverable: True

**`hallucinated_result`**
- Definition: The final answer includes specific claims not traceable to any tool observation in the trajectory.
- Example: Agent cites a figure that never appeared in any retrieved document.
- Typical severity: critical
- Typically recoverable: False

**`claimed_success_after_failure`**
- Definition: The agent reports task success despite the trajectory containing an unresolved critical failure.
- Example: A required write action failed with an error, but the final answer says 'completed successfully'.
- Typical severity: critical
- Typically recoverable: False

## Failure cascades

A failure can be the documented cause of a later failure in the same trajectory (`failure_events.is_cascading=True`, linked via `parent_failure_id`). Cascade edges are hand-curated to be directionally realistic — e.g. a retrieval problem can plausibly cause a downstream reasoning/output problem, but not vice versa. The complete edge list is `FAILURE_CASCADES` in `src/generation/taxonomy.py`, reproduced above under each failure type's "cascade targets." See `notebooks/01_exploratory_analysis.ipynb` and `notebooks/03_recovery_analysis.ipynb` for cascade frequency and recovery-rate analysis.

## Recovery strategy taxonomy

**`retry`** — Re-attempt the identical action unchanged, on the assumption the failure was transient.

**`alternative_tool`** — Switch to a different tool capable of achieving the same sub-goal.

**`reformulate_query`** — Re-issue a retrieval/search action with revised query terms.

**`verify_result`** — Insert an explicit verification step before proceeding or finalizing.

**`rollback`** — Undo or discard a partially completed action before re-attempting.

**`replan`** — Discard the current plan and construct a new decomposition of the task.

**`ask_for_clarification`** — Surface a request for additional information instead of guessing.

**`use_additional_evidence`** — Gather further supporting information rather than repeating the failed action.

**`change_execution_strategy`** — Alter how a step is executed (e.g. different arguments, narrower scope) without changing tools.

## Decision categories (trajectory_steps.decision_category)

`planning`, `retrieval`, `tool_selection`, `execution`, `verification`, `correction`, `finalization`

These describe *observable* agent behavior at each step. They are a deliberately coarse substitute for hidden chain-of-thought: the dataset records *what kind of decision* was being made, not the private reasoning text behind it. See docs/data_governance.md.
