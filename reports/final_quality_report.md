# Final Quality Report — Agent Failure Atlas 2026 (v2)

Checks run: 107 | Passed: 107 | Failed: 0

## Dataset statistics

- Total tasks: 1400
- Total agent_runs (trajectories): 3336
- Total trajectory_steps: 43477
- Total failure_events: 3802
- Total recovery_events: 4334
- Total evidence rows: 11737
- final_status distribution: {'success': 2007, 'partial_success': 839, 'failed': 490}
- runs with >=1 failure: 58.0%
- runs with >=2 failures (multi-failure): 31.6%
- clean success (no failure): 42.0%
- failure_category distribution: {'tool_use': 1138, 'state': 783, 'reasoning': 555, 'execution': 375, 'retrieval': 342, 'planning': 276, 'output': 252, 'verification': 81}
- cascading failures: 430 (11.3% of all failures)
- severity_level distribution: {1: 890, 2: 1539, 3: 1193, 4: 180}
- recovery success rate (when attempted): 60.3%
- recovery attempts >1 (repeated recovery): 532
- domain distribution: {'structured_extraction': 122, 'coding': 121, 'information_retrieval': 120, 'file_operations': 111, 'data_analysis': 110, 'api_workflows': 109, 'multi_step_reasoning': 107, 'web_research': 103, 'document_analysis': 102, 'rag': 101, 'planning': 101, 'constraint_satisfaction': 100, 'verification': 93}
- difficulty distribution: {'medium': 556, 'easy': 507, 'hard': 337}
- model distribution: {'gpt-4.1-class-a': 1008, 'claude-sonnet-cls': 662, 'llama-8b-class': 349, 'claude-haiku-cls': 339, 'gpt-4.1-mini-cls': 335, 'llama-70b-class': 333, 'mixtral-8x7b-cls': 310}

## Validation checks

| Check | Status |
|---|---|
| tasks.task_id unique | PASS |
| agents.agent_id unique | PASS |
| tools.tool_name unique | PASS |
| taxonomy.taxonomy_id unique | PASS |
| agent_runs.run_id unique | PASS |
| trajectory_steps.step_id unique | PASS |
| failure_events.failure_id unique | PASS |
| recovery_events.recovery_id unique | PASS |
| evaluations.run_id unique | PASS |
| evidence.evidence_id unique | PASS |
| agent_runs.task_id -> tasks.task_id | PASS |
| agent_runs.agent_id -> agents.agent_id | PASS |
| trajectory_steps.run_id -> agent_runs.run_id | PASS |
| failure_events.run_id -> agent_runs.run_id | PASS |
| failure_events.step_id -> trajectory_steps.step_id | PASS |
| recovery_events.run_id -> agent_runs.run_id | PASS |
| recovery_events.failure_id -> failure_events.failure_id | PASS |
| evaluations.run_id -> agent_runs.run_id | PASS |
| evidence.run_id -> agent_runs.run_id | PASS |
| evidence.task_id -> tasks.task_id | PASS |
| trajectory_steps.tool_name -> tools.tool_name (or null) | PASS |
| failure_events.parent_failure_id -> failure_events.failure_id (or null) | PASS |
| every agent_run has >=1 trajectory_steps | PASS |
| every agent_run has exactly one evaluations row | PASS |
| tasks.task_id has no unexpected nulls | PASS |
| tasks.task_domain has no unexpected nulls | PASS |
| tasks.difficulty has no unexpected nulls | PASS |
| tasks.task_description has no unexpected nulls | PASS |
| tasks.success_criteria has no unexpected nulls | PASS |
| agents.agent_id has no unexpected nulls | PASS |
| agents.model has no unexpected nulls | PASS |
| agents.provider has no unexpected nulls | PASS |
| agents.capability_tier has no unexpected nulls | PASS |
| agent_runs.run_id has no unexpected nulls | PASS |
| agent_runs.task_id has no unexpected nulls | PASS |
| agent_runs.agent_id has no unexpected nulls | PASS |
| agent_runs.final_status has no unexpected nulls | PASS |
| agent_runs.latency_ms has no unexpected nulls | PASS |
| trajectory_steps.run_id has no unexpected nulls | PASS |
| trajectory_steps.step_id has no unexpected nulls | PASS |
| trajectory_steps.sequence_number has no unexpected nulls | PASS |
| trajectory_steps.action_type has no unexpected nulls | PASS |
| trajectory_steps.decision_category has no unexpected nulls | PASS |
| trajectory_steps.step_status has no unexpected nulls | PASS |
| failure_events.failure_id has no unexpected nulls | PASS |
| failure_events.run_id has no unexpected nulls | PASS |
| failure_events.step_id has no unexpected nulls | PASS |
| failure_events.failure_type has no unexpected nulls | PASS |
| failure_events.failure_category has no unexpected nulls | PASS |
| failure_events.severity has no unexpected nulls | PASS |
| failure_events.severity_level has no unexpected nulls | PASS |
| failure_events.failure_sequence has no unexpected nulls | PASS |
| recovery_events.recovery_id has no unexpected nulls | PASS |
| recovery_events.failure_id has no unexpected nulls | PASS |
| recovery_events.run_id has no unexpected nulls | PASS |
| recovery_events.recovery_attempted has no unexpected nulls | PASS |
| recovery_events.final_outcome has no unexpected nulls | PASS |
| recovery_events.recovery_attempt_number has no unexpected nulls | PASS |
| evaluations.run_id has no unexpected nulls | PASS |
| evaluations.task_success has no unexpected nulls | PASS |
| evaluations.reliability_score has no unexpected nulls | PASS |
| evidence.evidence_id has no unexpected nulls | PASS |
| evidence.run_id has no unexpected nulls | PASS |
| evidence.task_id has no unexpected nulls | PASS |
| evidence.claim has no unexpected nulls | PASS |
| evidence.supports_claim has no unexpected nulls | PASS |
| trajectory_steps.decision_category in taxonomy | PASS |
| trajectory_steps.action_type in taxonomy | PASS |
| trajectory_steps.step_status in taxonomy | PASS |
| failure_events.failure_type in taxonomy | PASS |
| failure_events.severity_level in {1,2,3,4} | PASS |
| recovery_events.recovery_strategy in taxonomy (when attempted) | PASS |
| agent_runs.final_status in {success, partial_success, failed} | PASS |
| agents.capability_tier in {high, medium, low} | PASS |
| trajectory_steps.sequence_number strictly ordered & unique per run | PASS |
| agent_runs.latency_ms >= 0 | PASS |
| agent_runs.input_tokens >= 0 | PASS |
| agent_runs.output_tokens >= 0 | PASS |
| agent_runs.total_tokens == input+output | PASS |
| agent_runs.tool_call_count >= 0 | PASS |
| agent_runs.unique_tools_used <= tool_call_count | PASS |
| recovery_events.recovery_latency_ms >= 0 | PASS |
| recovery_events.recovery_token_cost >= 0 | PASS |
| recovery_events.recovery_attempt_number >= 0 | PASS |
| evidence.relevance within [0,1] | PASS |
| evaluations.constraint_satisfaction within [0,1] | PASS |
| evaluations.grounding_score within [0,1] | PASS |
| evaluations.final_answer_score within [0,1] | PASS |
| evaluations.reliability_score within [0,1] | PASS |
| evaluations.tool_efficiency within [0,1] | PASS |
| evaluations.trajectory_efficiency within [0,1] | PASS |
| evaluations.recovery_success_rate within [0,1] or null | PASS |
| no fully duplicate rows in trajectory_steps | PASS |
| no fully duplicate rows in agent_runs | PASS |
| no fully duplicate rows in failure_events | PASS |
| agent_runs.failure_count matches count of failure_events per run | PASS |
| failure_events.failure_sequence forms 1..N per run with no gaps/dupes | PASS |
| every is_cascading=True failure has a non-null parent_failure_id | PASS |
| every is_cascading=False failure has a null parent_failure_id | PASS |
| cascading failure's parent_failure_id belongs to the same run | PASS |
| cascading failure's parent_failure_id precedes it in failure_sequence | PASS |
| cascading failure_type is a documented FAILURE_CASCADES edge from its parent's failure_type | PASS |
| recovery_events.recovery_attempt_number is [0] (not attempted) or 1..N per failure | PASS |
| every failure_events.step_id has step_status in {error, recovered} | PASS |
| no step with step_status='ok' contains failure-indicating text in observation | PASS |
| noisy near-miss step text occurs in both failing and non-failing runs (not a leakage proxy) | PASS |
| evaluations.grounding_score matches mean(evidence.supports_claim) for its run | PASS |

## Publication Readiness

```
READY
```
