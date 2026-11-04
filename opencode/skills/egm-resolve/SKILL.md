---
name: egm-resolve
description: Evaluate review findings in Elephant context and apply only explicitly approved, current-revision documentation repairs
license: Apache-2.0
metadata:
  opencode/autoinvoke: false
---

<!-- Portions adapted from EGM, Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
Source: skills/egm-resolve/SKILL.md at
464db031e7dd1b9a79803ac8ea45f55c7c20c5bc.
Changes: immutable round evidence and separate resolution proposals/outcomes,
explicit per-revision approval, no implicit auto-accept or automatic next phase. -->

# Resolve with Elephant

Run only as Elephant. First read [shared workflow rules](../../resources/standards/workflow.md),
[assignment/result contract](../../resources/standards/goldfish-report.md),
and [resolution template](../../resources/templates/resolution.md).
If a required resource is missing, stop and name it. Do not change permissions.

## 1. Establish the actual findings

Read the specified round report, its snapshot, current original target, and
review-state.md. Ask only for missing paths or ambiguous scope, one question at a
time. Do not guess the latest report from a different topic. Inspect available
raw reviewer results and their validation/completion statuses. Incomplete review
coverage stays incomplete even if partial findings can be discussed.

Compare the current target with the reviewed snapshot. If it changed, mark review
coverage stale and re-evaluate each affected finding against current content;
never apply old line-based replacements blindly. Confirm the current revision
and proposed resolution scope with the user. A review request or invoking this
skill is not approval to edit the target. If outside the write boundary, discuss
findings but stop before repairs; do not edit a snapshot as a substitute.

## 2. Propose a disposition, not a verdict

Retain every raw ID, original severity, evidence, and reviewer provenance. For
each issue, propose one action:

- PROPOSE FIX: explain why it is valid and give exact current text/location and
  proposed replacement, or a precise structural insertion/removal.
- CONTEST: cite checkable evidence in the reviewer's allowed material. "We meant
  this" or hidden conversation is not evidence. Do not dismiss a genuine
  comprehension gap using knowledge absent from the target.
- ESCALATE: the decision requires private context, a new trade-off, or evidence
  outside the reviewer inputs. Ask the user; do not silently incorporate it.
- ACCEPT RISK: propose leaving an issue unresolved with concrete consequences.
  Only the user's explicit acceptance settles it; silence or "continue" does not.
- DEFER NIT: leave nonblocking editorial work recorded. Do not secretly fix it or
  use deferral to relabel a Blocker/Major.

Write reviews/round-NN-resolution-KK.md using a new resolution number and the
template. Keep the sealed round report and snapshot unchanged. Include exact
proposed edits, outstanding coverage, conflicts, and the current target revision.
Set the pending action in state. Link the proposal, highlight escalations and
risks, then ask one question: approve named fixes/the displayed batch, discuss
items individually, accept specific risks/contests, or make no changes. Wait.

## 3. Apply only the approved scope

An explicit "apply all proposed fixes" approves only the displayed PROPOSE FIX
items for the displayed revision. It does not accept risks/contests, resolve
escalations, approve another round, or authorize implementation. Ambiguous
"continue" means no target edits; clarify the next action instead of inferring
acceptance. An item-by-item discussion also pauses at each consequential choice.

Before editing, reread the target and ensure the approved text still matches.
If someone changed it or the proposed edits conflict, stop and obtain revised
approval. Apply approved documentation changes only. Increment the revision,
check structural coherence, and mark affected section approvals/reviews stale.
Record applied fixes as fixed-unverified, not verified or automatically resolved.
Never change the reviewed snapshot or raw findings to make the repair look valid.

Write a separate reviews/round-NN-resolution-KK-outcome.md with the actual user
response, applied/withheld items, before/after revision, accepted dispositions,
and verification still needed. Update the state ledger without erasing history.
No-change and partial decisions leave unaddressed findings open unless the user
explicitly settles them. Preserve rejected or superseded proposals as history.

## 4. Pause before further work

Summarize the outcome and remaining risks, link the artifacts, and ask one next
question: run another freshly confirmed review round, return to drafting, or
pause. Do not automatically loop, announce convergence after repairs, or hand off
to implementation. A new round uses egm-review with its own approval and snapshot.
