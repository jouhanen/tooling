---
name: egm-draft
description: Turn an agreed concept or supplied notes into a section-by-section design with explicit approval checkpoints
license: Apache-2.0
metadata:
  opencode/autoinvoke: false
---

<!-- Portions adapted from EGM, Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
Source: skills/egm-draft/SKILL.md at
464db031e7dd1b9a79803ac8ea45f55c7c20c5bc.
Changes: personal design template, bounded destination, revision/state tracking,
no shell identity lookup, author may accept recommendations, explicit handoff. -->

# Draft with Elephant

Run only as Elephant. First read [shared workflow rules](../../resources/standards/workflow.md)
and the [design template](../../resources/templates/design.md). If a required
resource is missing, stop and name it. This skill does not change permissions.

## 1. Confirm the starting point

Read the explicitly supplied concept or notes. If none are supplied, use only
the current confirmed topic's concepts.md; if that is absent, ask for the source
or discuss missing requirements in chat. Do not search unrelated topics and
silently choose their brief. A standalone draft from user notes is valid; do not
require a brainstorm skill run first.

Summarize the problem, scope, key decisions, and unresolved choices. Confirm the
artifact destination and obtain approval to start drafting from this context.
If the user already explicitly approved this exact transition, record it instead
of asking again. Read existing design.md and state before writing; ask whether
to continue/revise existing work rather than overwriting it.

## 2. Draft one section at a time

Use design.md in the confirmed directory. Start with a draft status and monotonic
revision. Use the template's sections in order: problem/goals/non-goals,
requirements, architecture/data flows, interfaces/data models, alternatives,
failures/security, rollout/rollback, implementation phases, tests/acceptance,
and open decisions/accepted risks. Leave unwritten sections clearly pending;
do not fill them speculatively just to complete the template.

For each section:

1. Read relevant approved sources and explain consequential choices in chat when
   they need a decision. Preserve choices already made unless new evidence changes
   the trade-off; disclose such changes and ask the user.
2. Write that section only, plus revision/status bookkeeping. Record its status
   as pending in review-state.md. Include paths and concrete evidence without
   claiming that unrun tests or unseen interfaces are verified.
3. Link the design, summarize material additions, and ask for section approval
   or requested revisions. End the turn and wait. Approval of one section does
   not approve the rest. Requested revisions return that section to pending.
4. Apply explicitly requested changes, increment the revision, and re-present
   material changes for approval before moving on.

Describe architecture and contracts rather than generating application code.
Implementation phases name Create/Modify/Delete intent, affected components,
dependencies, verification, and rollback where relevant. Leave ordinary coding
choices to Build, not unresolved architectural or product decisions. Do not run
commands, generate patches for application files, or turn a draft into code.

## 3. Reconcile and review

Reread the predecessor and current design. List contradictions and new material
architectural/interface/dependency decisions, quoting the relevant passages.
Ask the user to settle each consequential discrepancy before calling the draft
aligned. Neither the brief nor the new draft wins automatically.

Once sections are approved and discrepancies addressed, offer egm-review on the
current design revision. Load it only if the user requests review, and let it
confirm the preset, scope, and reading list. Do not self-certify independent
review or treat a skipped review as passed. Revisions from egm-resolve can make
section approvals stale and require renewed approval.

## 4. Stop at implementation approval

State the current design path/revision, review coverage, unresolved risks, and
acceptance criteria. Ask for approval of implementation of that specific revision
only when the user is ready; they may pause or deliberately accept disclosed
review limitations. Record their exact choice, then hand off to Build. Do not
implement or regard review completion as implementation approval.
