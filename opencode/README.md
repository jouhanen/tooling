# OpenCode V2 workflow package

This directory will contain the personal Elephant/Goldfish workflow. It is not
currently an installable OpenCode configuration.

## Package boundaries

| Component | Responsibility | Status |
| --- | --- | --- |
| `agents/elephant.md` | Persistent design discussion, drafting, and review coordination | Authored; offline checks only |
| `agents/goldfish-*.md` | Fresh, specialized, read-only reviews | Planned |
| `skills/` | Brainstorm, draft, review, and resolve procedures | Planned |
| `commands/` | Explicit entry points selecting Elephant | Planned |
| `resources/templates/` | Concept, design, and durable review-state templates | Authored |
| `resources/standards/` | Shared review standards | Planned |

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

An installer will be added after the agents and workflows. Until then, do not copy
this directory over `~/.config/opencode` or an existing project's `.opencode`
directory. [Offline contract checks](../tests/README.md) are available, but native
host enforcement and live model behavior have not been verified.

The intended installer will support project and global destinations, preview
changes, detect collisions, track owned files, and preserve unrelated settings.
Live model checks will require separate authorization.

## Elephant and artifacts

`agents/elephant.md` uses native V2 frontmatter without a model override. It does
not override Build, Plan, or the default agent. The prompt is self-contained for
exploration and drafting; review skills and named Goldfish agents will arrive in
later phases. It must stop rather than simulate a missing reviewer or skill.

The user confirms a topic and destination before the first write. The default is:

```text
docs/designs/<topic>/
  concepts.md
  design.md
  review-state.md
  reviews/
    round-01.md
```

Templates under `resources/templates/` are authoring aids. The future skills and
installer will expose their installed resource locations. Elephant's standalone
prompt includes the required field lists without relying on a sibling checkout
or assuming that relative agent-body links are automatically resolved.

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

See [third-party notices](../THIRD_PARTY_NOTICES.md) before adding or adapting EGM
material. No runtime component may depend on a sibling EGM checkout.
