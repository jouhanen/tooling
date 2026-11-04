# OpenCode V2 workflow package

This directory will contain the personal Elephant/Goldfish workflow. It is not
currently an installable OpenCode configuration.

## Package boundaries

| Component | Responsibility | Status |
| --- | --- | --- |
| `agents/elephant.md` | Persistent design discussion, drafting, and review coordination | Planned |
| `agents/goldfish-*.md` | Fresh, specialized, read-only reviews | Planned |
| `skills/` | Brainstorm, draft, review, and resolve procedures | Planned |
| `commands/` | Explicit entry points selecting Elephant | Planned |
| `resources/` | Shared standards and artifact templates | Planned |

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

An installer and tests will be added after the agents and workflows. Until then,
do not copy this directory over `~/.config/opencode` or an existing project's
`.opencode` directory.

The intended installer will support project and global destinations, preview
changes, detect collisions, track owned files, and preserve unrelated settings.
Live model checks will require separate authorization.

See [third-party notices](../THIRD_PARTY_NOTICES.md) before adding or adapting EGM
material. No runtime component may depend on a sibling EGM checkout.
