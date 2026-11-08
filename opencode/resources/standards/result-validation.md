<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Original personal workflow validation checklist. -->

# Validate a reviewer result before synthesis

Elephant applies this checklist to every native child result. Runtime validation
is prompt-driven: Elephant cannot run shell, Code Mode, or the operator's Python
reference validator. Offline validator tests do not establish model compliance.

Before synthesis, record each check's pass/fail/unverified outcome and supporting
native message/tool reference or specific failed field in the attempt artifact.
Do not replace these outcomes with a blanket checklist-passed statement. Required
checks that fail or cannot be established prevent accepted coverage. Native
completion and contract validity are separate: a completed tool can return an
invalid declaration.

Validate the assignment first. All path fields, including DiscoveryRoots, use
normalized POSIX spelling: no parent traversal, redundant separators, dot segments,
or trailing slash except `/` itself. Propose corrected paths before approval;
never rewrite sent assignments to make validation pass. Invalid approved inputs
need a corrected plan and a new round, not a retry with changed inputs.

1. Confirm a real native dispatch and completion for the expected named reviewer
   and current assignment. Keep available identifiers; never invent absent trace
    records. Model text alone is not native execution evidence. Missing completion
    means incomplete workflow coverage even with a completed JSON declaration.
    Copy session IDs directly from native tool results and cross-check the attempt
    artifact and stage log. If native child read records are available, inspect
    them instead of describing those reads as model-declared only.
2. Require exactly one JSON object, without fences, extra prose, duplicate keys,
   non-JSON constants, or unknown top-level fields. Do not rewrite malformed output
   into acceptance. Expected keys are reviewer, status, target, revision, round,
   scope, reads, missing_inputs, summary, and findings.
3. Match reviewer, target snapshot path, revision, round, and scope to the assignment.
   Round is a positive integer, not boolean or a string. For incomplete output,
   unavailable identity fields may be null, but a conflicting non-null value is
   invalid. Reviewer must always be the expected registered ID.
4. Require status completed/incomplete, summary a nonempty string, reads an array,
   missing_inputs an array of nonempty strings, and findings an array. Incomplete
   must explain missing inputs/evidence. Completed requires all identity fields
   and empty missing_inputs; it is not design approval or a clean grade.
5. Each read has only path and coverage, both nonempty strings. Completed results
   must declare entire file coverage for the target, supplied standard if any,
   and every required ReadingList file. Multiple actual slice reads may truthfully
   be aggregated as one entire file declaration only after all content was read.
   Partial coverage cannot count as complete. Reads outside the explicit inputs
   or approved discovery roots are invalid; comprehension permits only the target.
   A declaration is not independent proof of a read: compare native tool records
   where available and disclose unverified whole-file coverage.
6. Each finding has exactly id, severity, scope, evidence, rationale,
   recommendation, and certainty. All are nonempty strings. IDs follow
   `<reviewer>-<round>-<n>` with n assigned in output order from 1, without gaps.
   Severity is Blocker/Major/Nit, sorted in that order; certainty is confirmed/risk.
    Evidence names concrete target/source material; check citations rather than
    fabricating them. Risk rationales must name relevant conditions. Preserve
    original severity even when Elephant proposes a contest.
    Check all seven fields on every finding, even when its prose is plausible.
    Missing certainty is invalid; do not infer confirmed/risk and insert it.
7. Completed comprehension must retain both paraphrase labels: "What this
   proposes:" and "How the existing system works, per this document:". Its
   assignment has no reading list, standard, or discovery roots beyond the target.
8. Empty findings means no issues reported only for the completed assigned scope.
   Wrong identity, unread required inputs, malformed results, and failed native
   tasks cannot become zero-findings passes. An unanswered design question is
    usually a finding, not missing assignment data.
9. Compare the saved raw block with the native reviewer payload before synthesis.
   Preserve payload text verbatim, including missing fields, whitespace, and key
   order; parsing and reserializing is not a verbatim copy. Keep native wrappers
   separate and use a longer fence when necessary. Put parent interpretation and
   validation notes outside the raw block. If exact copying cannot be established,
   mark evidence preservation incomplete rather than inventing a passing result.

On invalid output, retain the failed attempt unchanged and follow the skill's
one-fresh-session retry rule with identical approved inputs. Do not add fields,
fix JSON, or ask the same child to rewrite its result into acceptance. A later
discovered evidence error requires a separate erratum and current-state correction,
not edits to sealed history. Preserve historical findings without treating invalid
coverage as accepted or its omissions as no findings.

The read-only reference implementation is `scripts/review_contract.py` in the
repository. An operator may supply assignment/result JSON files to it. It checks
declarations and syntax only; it cannot verify filesystem identity, symlinks,
actual tool execution, completeness of reasoning, approvals, or context isolation.
It is development tooling, not a permission granted to Elephant or a required
runtime dependency of these Markdown skills.

Operator CLI exit codes: 0 for a valid completed declaration, 2 for a valid
incomplete declaration, and 1 for invalid or unreadable input. Exit code 0 still
does not establish native execution, whole-file reads, design approval, or isolation.
