# Repaired workflow: live follow-up — 2026-11-08

## Outcome and scope

**Partial live acceptance; native malformed-response handling remains
unverified.** This follow-up used a disposable word-counter design project and
the existing Elephant session. It is separate from the earlier
[live audit](2026-11-08-live-audit.md), whose historical failures and evidence
remain unchanged. The project design and its findings are fixtures, not tooling
defects. No application implementation or application tests were performed.

At the operator's checks, the tooling candidate was commit
`8be254ad8a4e0da807d2f0610b1de66c7aa85030` with a clean tooling worktree before
this documentation update. All 26 installed project-local files matched both
their installation manifest and the tooling source; the manifest source digest
was `ba8576540ab4428a2449ee9102ec01934d7ca412abadc49d3dc6b40bb2c54df2`.
These are check-time identities, not proof of every historical run-start state.
The host reported OpenCode 2.2.6 at the later check; its exact version throughout
the exercise was not independently established. The parent session reported
`openai/gpt-6-luna-fast`, medium, at the later check; do not infer that every
child or earlier turn used that model. Full inherited instructions and policy,
individual child model settings, and all host context were not independently
inventoried. Private project artifacts and native records retain detailed
provenance; this public summary omits paths and session identifiers.

## Observed live checkpoints

| Check | Evidence and limits |
| --- | --- |
| Concept, drafting and approvals | Concept review, sequential drafting pauses, a requested revision, and stale section-approval detection after an outside edit were exercised. |
| Focused design review | Round 2's six saved assignments and raw payloads matched native records and passed the operator declaration validator; native records showed full required reads. Unnecessary retries occurred because unavailable parent-side read traces were treated as incomplete coverage. |
| Follow-up review | After the read-declaration/trace distinction was repaired, Round 3 used three fresh reviewers without unnecessary retries. The operator verified assignments, raw payloads, valid declarations, full required native reads, and a byte-identical target snapshot before later edits. This does not verify the later fixes. |
| Selective resolution | Elephant proposed fixes before editing; one was approved and applied while others were deferred without accepting risks. Later approved fixes were recorded as fixed-unverified. |
| Implementation handoff | Implementation approval was recorded with disclosed review gaps; Elephant handed off to Build without implementing. Disclosure is not acceptance of individual risks. No convergence was claimed. |
| Stale design coverage | After a one-reviewer Round 4, an outside edit changed target content without changing its revision label. On resume, Elephant detected the difference, marked earlier coverage and implementation approval stale, and paused. The clean streak was already zero, so resetting a nonzero streak was not tested. |

The run also exposed friction: Elephant initially failed to load the review skill
and then misresolved its shared-resource paths until directed to the installed
locations. The handoff described Round 3 native reads as unavailable even though
an independent operator audit had found them, and overstated disclosed gaps as
accepted risks. The private operator addendum records the corrected evidence;
these observations are not erased by later successful checks.

## Malformed-result checks

Two fresh native reviewers in a separately labelled fault-injection exercise
were asked to omit a required finding field. Both included it. Their outputs were
preserved and did not count as product-design coverage, but no malformed native
response reached Elephant; neither attempt tests rejection of one.

The operator then copied an existing assignment and valid result into a clearly
labelled synthetic saved fixture and removed only one finding's `certainty`.
The operator validator rejected the missing field. Asked to validate the saved
fixture, the live Elephant identified the omission, rejected completed coverage,
and said not to repair it or treat it as a native design review. The fixture's
SHA-256 was unchanged before and after the check. This is a **live model test of
saved synthetic-result validation**, not a native dispatch-response test; retry
handling and preservation of a malformed native response were not demonstrated.
The fixture explicitly described the removed field, so this is not a blind test.

## Remaining limits

- Deterministically exercise malformed native-response rejection, exact raw
  preservation, and the bounded fresh-retry path without counting injected
  material as genuine review coverage.
- Separately test invalidation of a nonzero clean streak if that behavior is
  required for acceptance.
- The workflow validation is instruction-driven, not machine-enforced at runtime.
  This follow-up does not establish general context, filesystem, or process
  isolation, nor support across models, versions, profiles, or policies.
- Additional real-model tests require authorization and an appropriate cost
  limit. Do not upgrade the earlier historical audit or this follow-up to a full
  pass based on synthetic fixtures or scripted probes.
