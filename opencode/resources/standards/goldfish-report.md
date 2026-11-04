<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Original personal workflow protocol; not copied from an upstream file. -->

# Goldfish assignment and result contract

This is the shared authoring contract for the seven personal Goldfish agents.
Each agent embeds the necessary rules so it can run without reading this file.
In particular, comprehension must not read a separate protocol or standard file.
The orchestration skill applies the [validation checklist](result-validation.md)
before synthesis. This document does not verify native tool records; the runtime
checklist is prompt-driven, not automatic machine enforcement.

## Assignment

| Field | Required value |
| --- | --- |
| Target | Explicit local file path, preferably an immutable round snapshot |
| Revision | Nonempty document revision label |
| Scope | `full file` or an unambiguous target section; line ranges refer to this target revision |
| Round | Positive integer assigned by Elephant |
| Task | `concept` or `design`; calibrate expectations to document maturity |
| ReadingList | Explicit list of required local file paths; an empty list is valid |
| Standard | Explicit local file path or `none` to use the embedded review lens |
| DiscoveryRoots | Optional approved local directories for bounded source discovery; defaults to empty |
| OriginalTarget | Optional original document path for relative-link provenance; not an additional readable input |
| Objective | Optional concise review objective; never the parent's persuasive design rationale |

Comprehension requires an empty ReadingList, Standard `none`, and absent or empty
DiscoveryRoots. It reads the entire target and no other files. Other reviewers
read the target, supplied standard, and every ReadingList file. Discovery is
limited by prompt to approved roots, not enforced as a per-assignment read rule.
No reviewer receives the design conversation or another concurrent review result.

Missing, conflicting, inaccessible, or partially unread required inputs mean
`incomplete`. Missing evidence for a core claim also means `incomplete`, not a
false statement that the claim was verified. Findings from completed portions may
still be returned. Do not turn a document defect into a missing-input condition
merely because the design fails to answer a question; record it as a finding.

## Result

Return one JSON object without Markdown fences or extra prose, with these keys:

| Key | Type and meaning |
| --- | --- |
| reviewer | Exact named Goldfish ID |
| status | `completed` or `incomplete`; not a passing grade or user approval |
| target | Supplied target path; null if unavailable |
| revision | Supplied revision label; null if unavailable |
| round | Supplied positive integer; null if unavailable |
| scope | Supplied scope string; null if unavailable |
| reads | Array of objects containing `path` and `coverage` strings for actual successful reads |
| missing_inputs | Array of concrete missing-input or missing-evidence descriptions; empty only when none are missing |
| summary | Concise assessment and verification limits |
| findings | Array of finding objects, ordered Blocker, Major, then Nit |

For `completed`, target, revision, round, and scope must be present, all required
reads and the audit must be finished, and missing_inputs must be empty. For
`incomplete`, missing_inputs must explain the failure. Empty findings in an
incomplete result never means no issues were found. A reviewer claiming completed
reads is not independent proof that those tool calls occurred.
Completed declarations must include coverage `entire file` for every required
input. Multiple successful slice reads can truthfully be aggregated only after
all content has been read. Partial coverage remains partial. Paths use normalized
POSIX spelling without parent traversal; use consistent exact paths across the
assignment, result, and evidence. This does not prove canonical filesystem identity.

Each finding contains exactly these fields:

| Key | Meaning |
| --- | --- |
| id | `<reviewer>-<round>-<n>`; n follows output order from 1 without gaps |
| severity | `Blocker`, `Major`, or `Nit` |
| scope | Target section or actual target line range |
| evidence | Concrete target wording and relevant inspected source paths; no invented citations |
| rationale | Why the issue matters under the stated requirements |
| recommendation | Actionable correction or decision needed |
| certainty | `confirmed` for an evidenced discrepancy or `risk` for a conditional concern |

A Blocker prevents the stated goal or safe implementation. A Major materially
affects correctness, clarity, or feasibility. A Nit is nonblocking polish. Risk
findings must name the condition that makes the risk relevant, not present a
hypothetical as a confirmed defect. Do not invent findings to meet a quota.

For comprehension, summary must include "What this proposes:" and "How the
existing system works, per this document:". A paraphrase must be grounded only in
the target, including when it fails to explain current behavior.

Elephant preserves result provenance and assigns dispositions separately. Do not
ask a reviewer to revise its conclusion to match another reviewer, and do not use
this report as authority to edit the target or proceed to implementation.
