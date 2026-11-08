# OpenCode V2 workflow package

This directory contains the personal Elephant/Goldfish workflow package. Use the
opt-in installer rather than copying it over an existing OpenCode profile. Native
discovery and sampled tool boundaries passed scripted 2.2.5 probes. A
[live audit](verification/2026-11-08-live-audit.md) found validation and evidence
failures; a [repaired-workflow follow-up](verification/2026-11-08-live-follow-up.md)
exercised additional checkpoints, but full acceptance remains pending.

## Package boundaries

| Component | Responsibility | Status |
| --- | --- | --- |
| `agents/elephant.md` | Persistent design discussion, drafting, and review coordination | Native discovery and sampled write/dispatch boundaries probed |
| `agents/goldfish-*.md` | Fresh, specialized, read-only reviews | Native discovery/dispatch and sampled read/skill boundaries probed |
| `skills/` | Brainstorm, draft, review, and resolve procedures | Partial live retest of repairs; native malformed-response handling remains unverified |
| `commands/` | Explicit entry points selecting Elephant in the current session | Native selection and skill-loading paths probed |
| `resources/templates/` | Concept, design, and durable review-state templates | Authored |
| `resources/standards/` | Workflow, assignment/report, and validation contracts; substantive review lenses embedded in agents | Authored |

The former V1 configuration and global Git/GitHub safety instructions have been
removed from this repository. This does not remove copies previously installed
elsewhere or change the running OpenCode configuration.

## Runtime contract

- Build and Plan remain independent; the installation must not change the user's
  default agent or provider/model configuration.
- Elephant writes design and review documentation, not application code.
- Goldfish return findings to Elephant; they do not edit files or launch agents.
- Reviewers receive an explicit assignment and reading list, not the design
  conversation. A failed reviewer is incomplete, not a review with zero findings.
- Human approval is required at the workflow's decision and revision checkpoints.
- Tool permissions must be verified against the installed V2 host. They are not a
  filesystem sandbox or proof that all inherited context has been excluded.

## Installation and validation

See [installation](INSTALL.md) for the standard-library installer. It previews by
default and requires `--apply` to write. Project and global installations use file
discovery without rewriting opencode.json(c). It detects target-local collisions,
tracks file hashes, refuses modified-file updates, and preserves local edits on
uninstall. It does not reconstruct the full effective host registry.

[Offline checks](../tests/README.md) cover installation and workflow contracts.
[Native probes](VERIFY.md) cover discovery and specific dispatch/tool boundaries
on 2.2.5 with a scripted provider, not general enforcement or real model behavior.
Further live acceptance requires separate authorization. The follow-up provides
scoped live evidence for the repaired payload, not a full acceptance pass.

## Elephant and artifacts

`agents/elephant.md` uses native V2 frontmatter without a model override. It does
not override Build, Plan, or the default agent. The prompt is self-contained for
exploration and drafting. The four workflow skills and named Goldfish prompts are
authored. It must stop rather than simulate a missing reviewer or skill.

The user confirms a topic and destination before the first write. The default is:

```text
docs/designs/<topic>/
  concepts.md
  design.md
  review-state.md
  reviews/
    round-01.md
    round-01-target.md
    round-01-goldfish-design-attempt-1.md
    round-01-resolution-01.md
    round-01-resolution-01-outcome.md
```

Templates under `resources/templates/` are authoring aids. Skills resolve shared
resources via `../../resources/` from their reported skill base directory. The
installer preserves that layout. Elephant's standalone prompt includes
the required field lists without relying on a sibling checkout or assuming that
relative agent-body links are automatically resolved.

The agent denies all actions except local reads, globs, questions, designated
skills/reviewers, and Markdown writes under `docs/designs/`. External-directory
access asks for permission separately; sensitive `.env` reads are denied, except
`.env.example`. Grep is not allowed because it can bypass per-file read rules.
Shell, network, MCP, Code Mode, and arbitrary delegation remain denied.

OpenCode's permission `*` matches `/`, so `docs/designs/*.md` allows nested
Markdown files across that entire tree, not just the selected topic. The prompt
limits actual work to the confirmed topic. Alternate output destinations require
a separate explicit configuration adjustment; Elephant cannot make that change.
These are role-specific limits, not global Git restrictions or a sandbox.

`review-state.md` records revisions, approvals with their scope and actual user
responses, section checkpoints, reviewer results, finding dispositions, and the
next pending action. A revision label alone is not a content hash. After a resume
or external edits, Elephant rereads artifacts, marks affected approvals/reviews
stale when necessary, and confirms the next action with the user. A saved state
file cannot grant new permission or replace a missing conversational approval.

## Goldfish reviewers

| Agent ID | Lens |
| --- | --- |
| `goldfish-zoom-out` | Necessity, simplicity, reuse, and architectural direction |
| `goldfish-comprehension` | Target-only paraphrase, definitions, and logical connections |
| `goldfish-design` | Architecture, interfaces, failures, security, and resource assumptions |
| `goldfish-structure` | Organization, required coverage, and meaningful content rather than empty headings |
| `goldfish-style` | Precision, calibrated claims, and concise technical language |
| `goldfish-codebase` | Current-state accuracy and integration, without confusing proposed files with missing ones |
| `goldfish-readiness` | Actionable phases, contracts, rollout/rollback, and acceptance tests |

All are native V2 `mode: subagent` definitions without a model override. Their
IDs match Elephant's exact dispatch allowlist. Each prompt embeds its review lens,
read boundary, and JSON result contract; no sibling checkout or implicit agent
file includes are required. Discovery and selected tool boundaries were probed
on 2.2.5; they do not establish general isolation or live review compliance.

All deny actions by default and allow local reads, excluding sensitive `.env`
files except `.env.example`. Six also allow glob; comprehension does not. Writes,
shell, questions, skills, delegation, network, MCP, and Code Mode are denied.
External access is denied in source Goldfish policies. Global installs render
one external-directory exception for bundled resources in the six source-aware
reviewers, not comprehension; Elephant also gets that narrow resource exception.
Other review inputs outside the active location/worktree remain inaccessible to
Goldfish. Do not weaken that boundary generally to make a run complete.

Comprehension reads the target alone. Other agents use an explicit reading list
and optional approved discovery roots. Assignment-level file restrictions are
prompt rules, not dynamic read allowlists: all agents can technically read other
non-sensitive local files. Host-injected instructions can still be present.
Do not claim target-only filesystem isolation or absence of inherited context.

The [assignment and result contract](resources/standards/goldfish-report.md)
requires a target revision, scope, round, document maturity, reading list, and
standard selection (`none` is valid). Inaccessible or incomplete required reads
produce `incomplete`, not a passing review. Results include actual read coverage,
evidence, severity, recommendations, and conditional-risk versus confirmed-issue
labels. Completion is not design approval. An incomplete result's empty findings
must never be interpreted as no issues found.

The review skill applies a shared validation checklist before synthesis. Runtime
validation is prompt-driven, not a plugin-enforced machine check. The read-only
Python reference validator under `scripts/` is available to operators and offline
tests; Elephant cannot run it under its default policy. Neither validates actual
native execution or proves context isolation on its own.

See [the workflow guide](WORKFLOW.md) for commands, focused/full presets,
stale-review handling, explicit resolution gates, and the operator validator.

See [third-party notices](../THIRD_PARTY_NOTICES.md) before adding or adapting EGM
material. No runtime component may depend on a sibling EGM checkout.
