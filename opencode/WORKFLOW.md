# Using the personal Elephant/Goldfish workflow

The prompts, skills, commands, and installer are available. Native discovery and
mechanical command/dispatch paths passed scripted 2.2.5 probes. A
[live audit](verification/2026-11-08-live-audit.md) demonstrated parts of the workflow
but found validation and evidence-preservation failures. A later
[live follow-up](verification/2026-11-08-live-follow-up.md) exercised the repairs
in part; native malformed-response handling and full acceptance remain unverified.
Use the [installer](INSTALL.md) with a disposable project first. These examples
describe intended use, not a passing live acceptance run.

## Entry points

| Command | Purpose |
| --- | --- |
| `/egm-brainstorm <idea>` | Discuss the problem, challenge assumptions, and agree on a concept |
| `/egm-draft <brief-or-notes-path>` | Draft a design one section at a time |
| `/egm-review <document-path>` | Confirm a review plan and dispatch fresh Goldfish |
| `/egm-resolve <round-report-path>` | Discuss findings and propose approved documentation changes |

All commands select Elephant and remain in the current session (`subagent: false`).
They explicitly load the matching skill; missing skills stop the workflow. No
command changes the default agent, provider, or model. The skills are hidden from
automatic model invocation but remain explicitly loadable by ID. Selecting the
skill alone in another agent does not switch its permissions: select Elephant.

Templates contain no shell blocks. However, OpenCode expands arguments before
shell preprocessing, outside agent tool permissions. Do not paste untrusted
document contents, executable shell-marker syntax, or arbitrary copied prompts
into command arguments. Use short trusted prompts, simple document paths, or an
ordinary message/attachment instead. A path/argument is not proof that its content
is trusted. Stored template quoting cannot make arbitrary arguments safe.

For example, after installation:

```text
/egm-brainstorm Add retryable webhook delivery to this service.
/egm-draft docs/designs/webhooks/concepts.md
/egm-review docs/designs/webhooks/design.md
/egm-resolve docs/designs/webhooks/reviews/round-01.md
```

Missing arguments lead to intake questions, not automatic writes or reviews.

## Discussion, drafting, and handoff

Elephant first investigates the problem and asks one consequential question at a
time. It challenges assumptions without inventing objections. Before the first
write, you confirm the topic/destination. Default output is under
`docs/designs/<topic>/`:

- `concepts.md`: the current direction, evidence, alternatives, assumptions, and
  decisions. Direction approval is not permission to draft or dispatch reviewers.
- `design.md`: sections drafted and approved individually, then reconciled against
  the predecessor. It does not contain an executable application implementation.
- `review-state.md`: actual approvals with scope, revisions, finding dispositions,
  review plans, clean streak, and the next pending action.

Elephant can only write Markdown under `docs/designs/`. Another output location
needs an explicit configuration adjustment outside this agent. The selected topic
and reviewer reading lists are prompt boundaries, not filesystem sandboxes.

Before implementation, approve the specific current design revision and any
disclosed unresolved risks or review gaps. Elephant records the handoff and asks
you to switch to Build. It does not implement code or commit on your behalf.

## Review presets

- **Focused concept:** zoom-out, design, comprehension, in one independent batch.
- **Focused design:** design, codebase, readiness, in one independent batch.
- **Full:** four ordered stages: zoom-out; comprehension; design/structure/style;
  codebase/readiness. It includes all seven lenses with a checkpoint after each
  stage. The target remains unchanged throughout the round.
- **Custom:** an explicitly confirmed subset of the seven named agents. Omitted
  coverage stays omitted; a partial preset is not a full review.

Choose scope, concept/design maturity, sources, standard selection, and optional
discovery roots. Empty sources and Standard `none` are valid; the embedded reviewer
lenses apply. Comprehension always receives the target alone. Full stages do not
inherit earlier findings or require upstream EGM's stage-specific reports. This
personal workflow is not a reproduction of upstream's numbered review pipeline.

You confirm the exact plan before dispatch. First invocation does not approve all
future rounds. The selected model is inherited unless separately overridden by
your configuration. One retry per failed assignment can increase model calls;
there are no paid tests or live calls in the offline suite.

## Round evidence and incomplete coverage

Each round gets a new number and immutable `reviews/round-NN-target.md` snapshot.
Assignments point to that snapshot; OriginalTarget preserves only path provenance
for relative references. Snapshot citations are not automatically live-file line
numbers. The round report records the original document and snapshot paths.

Raw assignments, outputs/errors, available native IDs, and validation outcomes
are preserved in separate `round-NN-<reviewer>-attempt-A.md` files. Round reports
append stage outcomes while running and are sealed at completion/interruption.
Later repairs do not rewrite snapshots, raw results, or sealed reports.

Copy reviewer payloads verbatim, with native wrappers separate, and cross-check
session IDs against native completions. Persist per-attempt validation outcomes
before synthesis; missing finding fields (including certainty) require rejection,
not parent-supplied repairs. Normalize proposed directory spelling before approval
(no trailing slash except `/`); never rewrite sent inputs to pass validation.
Later evidence errors use a separate dated erratum linked from current state;
affected coverage becomes incomplete without erasing historical findings.

Results must match the JSON contract and declared required reads. One fresh retry
is allowed; unavailable files/permissions must be corrected before retrying.
Changed inputs require a new plan/round. Failed, malformed, or incomplete reviews
never count as zero-findings passes. An incomplete full stage stops that pipeline.

If you edit the live target during a round, the round becomes stale. Relevant
source changes also invalidate affected coverage. Resume rereads current content,
state, and available snapshots and asks for confirmation. Revision labels are not
hashes; old approval records cannot silently authorize changed text.

## Resolution and stopping

Resolution proposes exact fixes, evidence-based contests, escalations, accepted
risks, or deferred Nits in a separate numbered proposal. You choose named items
or an explicitly displayed batch for the current revision. "Apply all proposed
fixes" does not accept risks or approve another review. Ambiguous "continue" does
not authorize target edits. Unaddressed findings remain open.

Approved changes increment the document revision and are `fixed-unverified`
until fresh evidence checks them. Prior findings do not become verified just
because a later reviewer omitted them. Outcomes preserve actual user decisions
separately from raw reviewer claims and proposed resolutions.

Another round always needs approval. Two consecutive clean rounds with unchanged
content, scope, reviewers, standards, and source inputs establish convergence for
that plan—not correctness or implementation approval. Unsettled Blocker/Major
findings, pending relevant verification, or stale/incomplete coverage prevent a
clean round; Nits do not. Explicitly accepted risks stay disclosed. Content or
plan changes reset the clean streak. At five rounds or detected churn, choose a
deliberate stop, bounded extension, or return to drafting. Stopping after one round
is valid but is recorded as halted, not converged.

## Operator declaration validator

The runtime skill follows a [checklist](resources/standards/result-validation.md).
That is instruction-driven validation, not enforcement by a plugin. Elephant
cannot execute the Python helper because shell and Code Mode are denied.

For operator diagnostics, extract the exact assignment and result JSON from the
private round artifacts into local files. Do not commit private prompts or
results just to run a check. The read-only helper needs only Python 3.10+:

```sh
python3 scripts/review_contract.py \
  --assignment /path/to/assignment.json \
  --result /path/to/result.json \
  --reviewer goldfish-design
```

Run from the repository root, not inside the target project. Exit codes are 0 for
a valid completed declaration, 2 for a valid incomplete declaration, and 1 for
invalid/unreadable input. The helper checks expected identity, fields/types,
whole-file read declarations, approved read paths, finding IDs/order, and target-only
comprehension. It rejects duplicate JSON keys and malformed wrappers, and never
repairs output into a passing result.

It does not prove that the declared reads happened, the entire file was actually
read, native dispatch completed, citations are true, approvals exist, or the child
context is isolated. [Native probes](VERIFY.md) establish only their specific
discovery/dispatch/tool cases; full acceptance of the repaired workflow still
needs separately authorized live verification.
