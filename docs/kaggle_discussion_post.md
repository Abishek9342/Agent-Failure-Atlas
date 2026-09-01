# Kaggle Discussion Post (Draft)

**Title: What Is the Hardest AI-Agent Failure to Recover From?**

---

I put together **Agent Failure Atlas 2026** because most agent datasets I
could find stop at prompt → response → pass/fail. That tells you *whether*
an agent succeeded, but not *how* it got there, *where* it broke, or
*whether it recovered*. The dataset tracks the full lifecycle — task, tool
calls, decisions, diagnosed failures (a run can have several, and they can
cascade into one another), recovery attempts, and outcome — all linked by
consistent IDs.

The taxonomy has 30 failure types across 8 categories (planning, tool_use,
retrieval, reasoning, state, verification, execution, output — full
definitions in `docs/taxonomy.md`), a documented numeric severity rubric
(1=minor to 4=critical), and 9 recovery strategies (retry, alternative_tool,
reformulate_query, verify_result, rollback, replan, ask_for_clarification,
use_additional_evidence, change_execution_strategy).

One design decision I'd specifically like feedback on: a handful of
failure types — `tool_loop`, `false_verification`, `unsupported_conclusion`,
`unauthorized_action`, `hallucinated_result`, `claimed_success_after_failure`
— are architecturally unrecoverable in this dataset (severity level 4,
"critical" in the rubric). My reasoning: these are cases where the agent's
own signal about its state is untrustworthy — it *thinks* it verified
something, or *claims* success when it didn't — so no retry/reformulate/
rollback strategy has anything reliable to act on. No recovery attempt is
ever generated for these in the data.

**Questions for the community:**

1. **Which failure category do you think is hardest to recover from in
   practice**, and does it match what's marked unrecoverable here? I'd
   guess `hallucinated_result` is the hardest to even *detect*, let alone
   recover from — curious if that matches real experience building agents.
2. **If you were building a recovery agent, which strategy would you try
   first for a `context_conflict` failure** (two retrieved sources
   disagreeing)? The taxonomy suggests `use_additional_evidence` or
   `incorrect_inference`-style replanning, but I'm not confident that's
   the right default.
3. **What failure type have you actually hit that doesn't map cleanly
   onto this taxonomy?** I tried to keep the 8 categories broad enough to
   cover most agent frameworks, but I'm sure there are real-world failure
   modes I'm missing.
4. **What additional fields would make this benchmark more useful for
   your own work?** E.g. would you want per-step latency broken out
   separately from recovery latency, a confidence score per step, or
   something else entirely?

This is a synthetic, fully-reproducible simulation (not real model
transcripts — see `docs/methodology.md` for why, and the honest tradeoffs
that implies), so I'm especially interested in whether the taxonomy,
cascade structure, and schema hold up as something worth building on,
independent of the specific numbers in this release.

Would love for researchers, students, and engineers working on agent
reliability to try it out and tell me where it breaks. Happy to iterate on
the taxonomy or schema based on what people actually need.
