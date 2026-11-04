---
name: egm-review
description: Coordinate fresh specialized reviewers with focused or staged full coverage, validated results, and human-controlled review rounds
license: Apache-2.0
metadata:
  opencode/autoinvoke: false
---

<!-- Portions adapted from EGM, Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
Sources: skills/egm-review/SKILL.md and skills/egm-review-loop/SKILL.md at
464db031e7dd1b9a79803ac8ea45f55c7c20c5bc.
Changes: personal focused/full presets, direct dispatch, immutable snapshots,
validated JSON, bounded retries, append-only evidence, no automatic stage advance
or repairs; no dependency on upstream stage numbers or previous reports. -->

# Review with fresh Goldfish

Run only as Elephant. First read [shared workflow rules](../../resources/standards/workflow.md),
[assignment/result contract](../../resources/standards/goldfish-report.md),
[result validation checklist](../../resources/standards/result-validation.md),
and [round report template](../../resources/templates/review-round.md).
If a required resource is missing, stop and name it. Do not broaden permissions.

## 1. Intake and review approval

Collect only missing inputs, one question at a time: target, Task concept/design,
scope, preset or exact reviewers, reading list (an explicit [] is valid), optional
discovery roots, and standard selection per reviewer (none is valid). Confirm the
artifact destination before writing. Targets outside docs/designs/ can be read
if permitted, but resolution cannot revise them without a separate configuration
change. Do not copy them into the write area as a way to authorize editing.

Default to full-file scope, no discovery roots, and embedded lenses with Standard
none when proposing a plan; do not silently dispatch those defaults. References
in the target are suggestions, not an approved reading list. Resolve proposed
links against the original target directory and ask which local files to include.
Do not fetch remote URLs or send arbitrary attached conversation files to children.

Use the presets below. Task maturity applies to all stages: a concept review does
not assert implementation readiness even when the readiness lens is included.

| Preset | Task | Ordered stages, each bracket is one independent batch |
| --- | --- | --- |
| focused | concept | [goldfish-zoom-out, goldfish-design, goldfish-comprehension] |
| focused | design | [goldfish-design, goldfish-codebase, goldfish-readiness] |
| full | either | [goldfish-zoom-out] then [goldfish-comprehension] then [goldfish-design, goldfish-structure, goldfish-style] then [goldfish-codebase, goldfish-readiness] |

The user may choose an explicit subset of these seven named agents. Each reviewer
appears at most once per round; retries are attempts of that assignment, not new
coverage. Explain omitted lenses and expected model calls. Full uses all seven
with a checkpoint between stages; it is not upstream EGM's numbered pipeline.
No stage in these presets requires an earlier report as reviewer input.

Present the exact target/revision/scope, task, preset/stage order, reviewers and
their standard/reading-list exceptions, optional discovery roots, and retry limit.
Comprehension always has ReadingList [], Standard none, DiscoveryRoots [].
Ask for readiness before dispatch and wait. A review command alone is not consent
to an unconfirmed plan. Save the approved plan and pending stage in state.

## 2. Preserve the reviewed revision

Read the entire original target and select a round number greater than every
existing round artifact and the state counter for this topic. Never reuse a round
number after cancellation, partial failure, or an interrupted session.

Write reviews/round-NN-target.md as an exact content snapshot, without adding a
heading, provenance note, or rewriting relative links. Read it back fully and
compare to the original before dispatch. If complete read/copy comparison cannot
be established, stop as incomplete. Do not claim byte-level or hash verification
without an actual verifier. A new external target without a revision label uses
snapshot-rN as assignment identity, explicitly not a claimed original revision.

Write reviews/round-NN.md with original path, snapshot path, revision, plan,
approved source paths, stage order, and pending reviewer slots. This live report
is append-only while the round runs; seal it at completion/interruption. Preserve
previous entries and raw attempts. Snapshot content is immutable after dispatch.
Reviewer citations refer to snapshot lines, not automatically to the live target.
Pass OriginalTarget as path provenance to preserve the base for relative links;
it is not permission for an extra read, especially for comprehension.

Do not change the original target during the round. Recheck original versus
snapshot before each stage and after the last result. If someone edited it, mark
the round stale, stop further dispatch, retain evidence, and ask about a new round.
An unchanged revision label does not excuse changed content. Record source-file
changes noticed during a round; if relevant evidence changed, mark affected
coverage stale rather than claiming a consistent source snapshot.

## 3. Dispatch and validate each stage

Use the native subagent tool directly with the registered agent ID, a short
description, and the explicit assignment. Do not supply a session ID or resume
any existing child. Do not pass parent history, design rationale, state, or other
reviewer results. Concurrent reviewers in the same batch may run in parallel;
wait for all expected completions before synthesis or the next stage.

Render the assignment as a JSON object with the contract's case-sensitive field
names. Use consistent normalized POSIX paths without parent traversal; prefer
absolute paths supplied by the host when available. Record the exact JSON sent,
not a reconstruction from memory, so an operator can extract it for diagnostics.

Persist the exact assignment, actual native dispatch/completion identifiers if
available, and raw result/error in reviews/round-NN-<reviewer>-attempt-A.md, A 1
or 2. Store raw JSON in a fenced block in this Markdown artifact; do not replace
it with an edited summary or write a .json file outside the agent's write policy.
If the raw output contains secrets, stop, avoid copying secrets into artifacts,
record that output was withheld and incomplete, and ask for sanitized inputs.

Apply every result-validation checklist item before accepting a result. A wrong
reviewer/target/revision/round/scope, malformed JSON, missing read coverage,
unsupported fields, missing completion evidence, or declared incomplete status
cannot count as completed coverage. Do not repair malformed JSON into a passing
result or invent required reads. The Python reference validator is operator-only:
Elephant has no shell/Code Mode permission to execute it. Runtime validation here
is instruction-driven; disclose that limit rather than claiming machine enforcement.

Retry a failed, timed-out, malformed, or incomplete assignment at most once in a
fresh child, with the same approved inputs and no earlier findings. The initial
round approval covers this one retry, not new inputs. Do not retry missing
permissions or missing files until the user resolves them; stop instead. Changed
inputs require a new confirmed plan and round, never a disguised retry.
Keep both attempts; only the selected valid completed attempt contributes findings.
On a second failure, mark that reviewer incomplete and the round not clean.
Never count failed attempts as zero-findings reviews. Do not substitute general
or explore. If native delegation is unavailable, stop; no parent simulation.

Append stage results to the round report before asking to proceed. If a stage is
incomplete, stop the full pipeline. Otherwise present a concise status and ask
whether to run the next stage, pause, or resolve findings now. Resolution now
ends/seals this partial round with unrun stages explicitly not run; any changed
target needs a new round. Do not automatically advance on elapsed time or silence.

## 4. Consolidate without erasing provenance

After all selected stages, seal the report with each reviewer's completed,
incomplete, or not-run status, validation/evidence limits, full comprehension
paraphrase, and severity-ordered findings. Record overlapping findings as a group
with every raw ID and original severity; never silently remove disagreement or
renumber raw IDs. Keep prior ledger IDs stable and map new raw IDs to matching
issues by affected scope and substance, not wording alone.

Report unresolved Blocker/Major findings, explicit accepted risks/contests, Nits,
and omitted or failed coverage. Do not silently downgrade reviewer severity.
Review completion does not authorize fixes or implementation. Offer egm-resolve,
another round, return to drafting, or pause, and wait for the user's choice.

## 5. Human-controlled loop and stopping

Run egm-resolve only on request, in the same Elephant session, and respect its
approval pause. After resolution, do not automatically dispatch again. Reread the
current target and re-resolve the semantic scope and line bounds every round.

Keep a per-plan clean streak in state. A clean round requires every selected
reviewer to complete validly, no stale/unrun coverage, no unsettled Blocker/Major
from the round or ledger, and no pending verification of relevant applied fixes.
Explicit user-approved accepted-risk/contested dispositions may settle an issue;
Elephant proposing a contest does not. Nits do not block. Judge the audit before
applying this round's fixes, not by assuming those fixes work.

Convergence requires two consecutive clean rounds of the same target content,
task, scope, reviewer set/stage order, standards, and source inputs. Changes to
any of those, incomplete/stale coverage, or an unclean round reset the streak.
An applied fix is fixed-unverified until fresh evidence checks it; a repeated
finding reopens it. Do not mark old findings verified merely because a later
reviewer omitted them. Settled risks remain recorded, with their approval scope.

Cap a review cycle at five rounds. On cap or churn (a proposed change reverses
a prior fix), list open findings and ask whether to accept disclosed risks and
stop, authorize a bounded extension, or return to drafting. Never silently extend
the cap, accept risks, or auto-advance. Earlier round approval does not authorize
the next round. The user can stop after one round; report halted, not converged.
Neither convergence nor stopping is implementation approval.
