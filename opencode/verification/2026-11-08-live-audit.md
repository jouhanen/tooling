# Live workflow audit and erratum — 2026-11-08

## Outcome and scope

**Partial live acceptance, with validation and evidence-preservation failures.**
This is a retrospective audit of a disposable static-portfolio design exercise,
not a passing end-to-end acceptance run. Brainstorm, section drafting, two focused
design review rounds, resolution, and renewed section approvals were exercised
with a real human. No implementation handoff or website implementation occurred.

The audit inspected the parent session, a separate alignment session, and all six
native child sessions through read-only OpenCode API requests. Native messages,
tool inputs/results, and local artifacts remain private; this report deliberately
omits personal paths, conversation contents, and session identifiers. The local
project's `reviews/2026-11-08-audit-erratum.md` retains exact provenance references.

## Candidate identity and limitations

- Parent session span (UTC): November 4, 20:19:29 through November 8, 18:41:27, 2026.
- Model in the inspected parent and reviewer records: `openai/gpt-6-luna`, `high`.
- Host at audit: OpenCode `2.2.5`; historical run version not independently established.
- Installation: project-local; 26 installed files matched their manifest and the
  source payload at audit, before the repairs accompanying this record.
- Manifest source digest: `93d37240cf36f6aab5bb5385a47edda47a47be3f23786e3fca961615aa28a2e6`.
- Tooling HEAD at audit: `592ca683f9e2c74e6d8cdac66cf040e6ed8d5c6d`; worktree clean
  before these repairs. This does not establish the run-start commit/dirty state.
- Run-start hashes, frontend/surface, complete inherited instruction/policy
  inventory, and explicit upfront model/profile/usage-budget authorization were
  not established by this audit. Current hashes cannot prove historical integrity.

The repaired source payload differs from the installed/tested candidate. Neither
the old scripted probes nor this live run establish live compliance of the repairs.
No package update, paid review, or acceptance rerun is part of this audit.

## Corrections to the historical reports

1. **Malformed output was accepted and altered.** Round 02 readiness omitted
   `certainty` on both findings in its native final message and the payload
   received by the parent. The saved attempt artifact added `certainty: confirmed`
   under its "Raw result" heading and labeled the declaration valid. No fresh
   retry occurred. This is a validation and evidence-preservation failure, not a
   valid declaration or an empty-findings pass. Retain the original findings as
   historical claims; their later approved fixes do not repair the review evidence.
2. **Both codebase assignments violate path spelling.** Round 02 and Round 03
   supplied a discovery root with a trailing slash. The operator validator
   rejects that spelling. This is an assignment/validator compatibility failure;
   it does not mean the native reads or reviewer execution failed. Do not strip
   the slash from historical assignments to turn those checks into passes.
3. **Native readiness IDs were transcribed incorrectly** in both reports and
   attempt artifacts. Actual children are identifiable through parent tool
   completions and native parent/child relationships. Exact corrections are in
   the private local erratum, not reconstructed identifiers in this report.
4. **Native full-file read evidence exists.** All six children have successful
   reads through the final lines of the required snapshot and concept. Reports
   describing all reads as merely model-declared understate available evidence.
   This does not establish general context isolation or reasoning quality.

The original sealed reports, snapshots, attempts, and resolution outcomes remain
unchanged. A separate local erratum and current-state correction supersede their
validation/coverage claims without rewriting historical findings or approvals.

## Retrospective operator validation

The audit ran the existing read-only declaration validator against the original
native assignments/results in memory, without repairing inputs:

| Reviewer | Round 02 | Round 03 |
| --- | --- | --- |
| design | Pass | Pass |
| codebase | Invalid assignment: trailing-slash discovery root | Invalid assignment: trailing-slash discovery root |
| readiness | Invalid result: both findings missing certainty | Pass |

These are retrospective checks, not proof that runtime validation was correct.
Native execution completed for all six reviewers; accepted coverage is a separate
question. Both rounds have incomplete accepted coverage and neither is clean.

The erratum's preserved readiness payload was subsequently compared as text with
the native final-message payload and matched verbatim. This checks the new copy,
not the original altered attempt artifact.

## Live checkpoint evidence

| VERIFY checkpoint | Observed evidence | Remaining gap |
| --- | --- | --- |
| 1. Brainstorm | Real questions, challenge to fictional-work presentation, destination confirmation before writing | None identified for this checkpoint |
| 2. Concept/review approval | Concept confirmation; separately approved design-review plans and input lists; fresh children and full reads | Concept review not run; concept and drafting authorization shared one response; validation failures above |
| 3. Draft | Sequential section writes and human pauses; ambiguous continue prompted clarification; contradictions reconciled with reapproval | Separately exercise concept approval versus drafting authorization |
| 4. Focused review | Snapshots, attempts, native completion/read evidence, provenance | Validation and exact-raw-preservation failures prevent full pass |
| 5. Resolve | Proposals before target edits; approved changes and revisions; fixed-unverified dispositions retained | Explicitly reject/defer a repair while approving another |
| 6. Follow-up | Three fresh Round 03 children; assignment messages did not forward earlier findings/history; no convergence claim | Full model-request context isolation not established |
| 7. Resume | Another session changed r10 to r12; original session detected stale plan and obtained approval for a new round | Separately demonstrate outside-edit/resume invalidating a section approval and affected coverage |
| 8. Handoff | Final message asked for implementation approval of r17 | Explicit approval and Build handoff not run |

## Repairs and required retest

The accompanying source changes make per-attempt validation records, exact raw
copy comparison, native-ID cross-checks, missing-certainty rejection, normalized
directory spelling, and separate errata explicit. Operator diagnostics name the
missing finding field and trailing-slash problem; regression tests ensure invalid
inputs remain unchanged. These are prompt/checker repairs, not machine-enforced
runtime validation or a new permission grant to Elephant.

Repair verification: `python3 -B -m unittest discover -s tests` passed all 92
offline tests on the local Python 3.14 environment. No live acceptance rerun or
native mechanical probe of the repaired payload was performed.

To complete acceptance, identify and authorize the repaired candidate before new
calls. Retest the review path and missing-certainty rejection with preserved raw
evidence; use a separately authorized fault-injection case for the latter, not a
fabricated genuine review. Exercise the remaining checkpoint gaps above. Keep
injection results distinct from design-review coverage and record every failure.
Use new approved plans/rounds rather than backfilling old retries. Record the
result in a new report; do not upgrade this historical run to passed.
